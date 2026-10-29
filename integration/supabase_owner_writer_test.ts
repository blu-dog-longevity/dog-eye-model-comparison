import {createGeminiOwnerWriter} from "./supabase_owner_writer.ts";
import {OBS_KEYS, type GeminiOwnerResult} from "./gemini_owner_backend.ts";
function assert(x:unknown,message:string){if(!x)throw new Error(message);}
Deno.test("transactional RPC writer uses only server-side API and expected fields",async()=>{
 let called=false;
 const mocked=async(input:RequestInfo|URL,init?:RequestInit)=>{
   called=true;
   assert(String(input).endsWith("/rpc/save_eye_owner_gemini_assessment"),"Wrong endpoint");
   const data=JSON.parse(String(init?.body));
   assert(data.p_photo_id==="12345678-1234-1234-1234-123456789abc","Missing photo reference");
   assert(data.p_model==="gemini-2.5-flash","Missing version");
   return new Response(JSON.stringify("12345678-1234-1234-1234-123456789abc"),{status:200});
 };
 const writer=createGeminiOwnerWriter({supabaseUrl:"https://example.supabase.co",serviceKey:"test-secret",fetcher:mocked as typeof fetch});
 const result:GeminiOwnerResult={photo_id:"12345678-1234-1234-1234-123456789abc",
  observations:Object.fromEntries(OBS_KEYS.map(k=>[k,{severity:"unclear",description:"Unknown"}])),
  display_state:"needs_review",owner_summary:"Please retake photo",
  comparison:{change:"unable_to_compare",previous_photo_id:null},limitations:[],actions:[]};
 const output=await writer({photo:{id:result.photo_id,dog_id:"d",eye_side:"left",storage_bucket:"dog-media",storage_path:"x",captured_at:null},
  result,model:"gemini-2.5-flash",promptVersion:"owner-v1"});
 assert(called,"Expected request");
 assert(output.displayResultId===result.photo_id,"Expected stored ID");
});
