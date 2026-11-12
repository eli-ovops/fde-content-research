import Foundation
import AVFoundation
import Vision
let input=URL(fileURLWithPath:CommandLine.arguments[1])
let out=URL(fileURLWithPath:CommandLine.arguments[2])
let asset=AVURLAsset(url:input)
let duration=try await asset.load(.duration).seconds
let tracks=try await asset.load(.tracks)
print("duration=\(duration),tracks=\(tracks.count)")
let gen=AVAssetImageGenerator(asset:asset)
gen.appliesPreferredTrackTransform=true
gen.maximumSize=CGSize(width:1080,height:1920)
gen.requestedTimeToleranceBefore=CMTime(value:1,timescale:10)
gen.requestedTimeToleranceAfter=CMTime(value:1,timescale:10)
let req=VNRecognizeTextRequest();req.recognitionLevel = .accurate
req.recognitionLanguages=["zh-Hans","en-US"];req.usesLanguageCorrection=true
var rows:[[String:Any]]=[]
var failures:[Double]=[]
for tick in 0..<20 {
 let sec=Double(tick)/2
 do {
  let result=try await gen.image(at:CMTime(seconds:sec,preferredTimescale:600))
  let text:String=try autoreleasepool {
   try VNImageRequestHandler(cgImage:result.image).perform([req])
   let obs=(req.results ?? []).sorted{$0.boundingBox.midY > $1.boundingBox.midY}
   return obs.compactMap{$0.topCandidates(1).first?.string}.joined(separator:"\n")
  }
  rows.append(["time":sec,"text":text])
 } catch {failures.append(sec); if failures.count < 3 {print("FRAME_ERROR \(error)")}}
 if tick%40==0 {print("\(sec)/\(duration)")}
}
let doc:[String:Any]=["input":input.path,"duration":duration,"sample_interval":0.5,"scope":"visible burned-in captions and visual text; not audio transcript","frames":rows,"failed_times":failures]
try JSONSerialization.data(withJSONObject:doc,options:[.prettyPrinted,.sortedKeys]).write(to:out)
print("saved \(out.path),frames=\(rows.count),failures=\(failures.count)")
