import { buildGeminiRequest, validateOwnerResult, OBS_KEYS } from "./gemini_owner_backend.ts";
function assert(cond: unknown, msg: string) { if (!cond) throw new Error(msg); }
const base = {
 photo_id:"photo-a", observations:Object.fromEntries(OBS_KEYS.map(k=>[k,{severity:"unclear",description:"Not clear"}])),
 display_state:"needs_review", owner_summary:"Unable to assess the photograph.",
 comparison:{change:"unable_to_compare",previous_photo_id:null}, limitations:["Low lighting"],actions:["Retake the photo"]
};
Deno.test("Gemini owner assessment may run without research results",()=>{
 const out=validateOwnerResult(base,"photo-a");
 assert(out.display_state==="needs_review","expected review");
});
Deno.test("Rejects accidental other dog/photo result",()=>{
 let failed=false;try{validateOwnerResult(base,"photo-b");}catch{failed=true;}
 assert(failed,"must reject wrong photo");
});
Deno.test("Rejects unverified comparison",()=>{
 let failed=false;try{validateOwnerResult({...base,comparison:{change:"increased",previous_photo_id:null}},"photo-a");}catch{failed=true;}
 assert(failed,"must require previous same-eye photo");
});
Deno.test("Rejects diagnosis claims",()=>{
 let failed=false;try{validateOwnerResult({...base,diagnosis:"Glaucoma"},"photo-a");}catch{failed=true;}
 assert(failed,"must reject diagnosis");
});
Deno.test("Gemini request includes supplied image only; no research dependencies",()=>{
 const req=buildGeminiRequest({mimeType:"image/jpeg",base64:"abc"},
 {photoId:"photo-a",eyeSide:"left",proSummary:{symptoms:[],interventions:[],vetFindings:[]}},"gemini-2.5-flash");
 assert(req.contents[0].parts.length===2,"must have text and image");
 assert(req.generationConfig.responseMimeType==="application/json","expect JSON");
});
