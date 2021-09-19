import QtQuick 2.0
import MuseScore 3.0
import FileIO 3.0

MuseScore {
      menuPath: "Plugins.MuseJackPlugin"
      description: "Plugin that allows the automatic writing of .mjck files. These files can be read by the MuseJack program to automatically link musescore Scores to video files."
      version: "1.0"
      
      property string mjackPrefix: "@mjack";
      FileIO {
            id: "mjack"
      }
      
      onRun: {
            if(typeof curScore === 'undefined'){
                  Qt.quit();
            }
            
            var p = curScore.path;
            var dirIndex = p.lastIndexOf("/");
            var dirName = p.substring(0, dirIndex + 1);
            var fileName = p.substring(dirIndex + 1, p.length - 5);
            
            mjack.source = dirName + fileName + ".mjck";
            
            var outputs = {}
            outputs.msczPath = dirName + fileName + ".mscz"
            outputs.mjckPath = mjack.source

            outputs.points = []
            //search first track/part for staff text annotations
            var track = 0;
            
            //tempo state keeping variables
            var tempo = 80 / 60; //asume the first tempo chosen is 80 BPM
            var previousTempoTicks = 0; //in midi ticks
            var previousTempoTime = 0; //in SECONDS
                      
            
            var segment = curScore.firstSegment();
            while(segment){
                  //staff text is stored as annotations on the segment.                 
                  var anns = segment.annotations;
                        if (anns && (anns.length > 0)) {
                              for (var annc = 0; (annc < anns.length); annc++) {
                                    var element = anns[annc];
                                    if (element.type == Element.STAFF_TEXT){
                                          if(element.text.startsWith(mjackPrefix)){
                                               var splits = element.text.split("\n")
                                               if (splits.length == 3){
                                                      var point = {}
                                                      point.path = splits[1]
                                                      point.videoTime = splits[2]
                                                      
                                                      //calculation of MSTIME
                                                      var ticksSinceLastTempoChange = segment.tick - previousTempoTicks
                                                      var timeSinceLastTempoChange = ticksSinceLastTempoChange / division / tempo
                                                      point.msTime = previousTempoTime + timeSinceLastTempoChange
                                                      outputs.points.push(point)
                                               }
                                          }
                                    }else if (element.type == Element.TEMPO_TEXT){
                                          var totalCurrentTempoTicks = segment.tick - previousTempoTicks;
                                          console.log("Ticks passed: " + totalCurrentTempoTicks.toString());
                                          previousTempoTime += totalCurrentTempoTicks / division / tempo
                                          
                                          tempo = element.tempo
                                          previousTempoTicks = segment.tick
                                          
                                          
                                    }
                               }
                        }
                  segment = segment.next
            }
            
            mjack.write(JSON.stringify(outputs, null, 2))
            console.log("this works")
            Qt.quit()
            
       
      }
}
