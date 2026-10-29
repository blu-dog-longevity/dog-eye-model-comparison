import {assessOwnerEye, type OwnerDependencies} from "./gemini_owner_workflow.ts";
import {OBS_KEYS, type GeminiOwnerResult} from "./gemini_owner_backend.ts";
function assert(cond:unknown,msg:string){if(!cond)throw new Error(msg);}
const photo={id:"p1",dog_id:"d1",eye_side:"left" as const,storage_bucket:"dog-media",storage_path:"private/p1.jpg",captured_at:null};
const fakeImage={mimeType:"image/jpeg" as const,base64:"a".repeat(100)};
const result:GeminiOwnerResult={photo_id:"p1",observations:Object.fromEntries(OBS_KEYS.map(k=>[k,{severity:"unclear",description:"Cannot determine"}])),
 display_state:"needs_review",owner_summary:"Please retake.",comparison:{change:"unable_to_compare",previous_photo_id:null},limitations:["Low light"],actions:["Retake"]};
const cfg={model:"gemini-2.5-flash",promptVersion:"owner-v1",geminiApiKey:"fake",maxImageBytes:20000};
function deps(log:string[]):OwnerDependencies{return {
  getEyePhoto:async()=>{log.push("photo");return photo;},
  assertCanViewDog:async(jwt,dogId)=>{log.push("auth");if(jwt!=="allowed"||dogId!=="d1")throw new Error("forbidden");},
  loadPrivateImage:async()=>{log.push("image");return fakeImage;},
  getPriorSameEye:async()=>null,
  getSanitizedProContext:async()=>({symptoms:[],interventions:[],vetFindings:[]}),
  callGemini:async()=>{log.push("gemini");return result;},
  saveOwnerAssessment:async()=>{log.push("save");return {displayResultId:"display1"};}
};}
Deno.test("Does not access private image before dog authorization",async()=>{
  const log:string[]=[];let denied=false;
  try{await assessOwnerEye({userJwt:"wrong",photoId:"p1"},deps(log),cfg);}catch{denied=true;}
  assert(denied,"must deny access");assert(log.join(",")==="photo,auth","must not load image or invoke Gemini");
});
Deno.test("Authorized owner path stores assessment once",async()=>{
  const log:string[]=[];const output=await assessOwnerEye({userJwt:"allowed",photoId:"p1"},deps(log),cfg);
  assert(output.displayResultId==="display1","expected display result");
  assert(log.join(",")==="photo,auth,image,gemini,save","unexpected processing sequence");
});
Deno.test("Reject mismatched historical eye",async()=>{
 const log:string[]=[];const d=deps(log);
 d.getPriorSameEye=async()=>({...photo,id:"p0",eye_side:"right"});
 let failed=false;try{await assessOwnerEye({userJwt:"allowed",photoId:"p1"},d,cfg);}catch{failed=true;}
 assert(failed,"must reject cross-eye history");assert(!log.includes("gemini"),"must not send mismatched history");
});
