/** Server-only transactional Gemini result writer.
 * Call only after JWT-based dog authorization and validated Gemini output.
 * This adapter invokes the restricted Supabase RPC function; it does not
 * authorize caller access itself and must never be imported by a client.
 */
import type {EyePhoto} from "./gemini_owner_workflow.ts";
import type {GeminiOwnerResult} from "./gemini_owner_backend.ts";

export function createGeminiOwnerWriter(config:{
  supabaseUrl:string; serviceKey:string; fetcher?:typeof fetch;
}) {
 if (!config.supabaseUrl.startsWith("https://") || !config.serviceKey)
   throw new Error("Secure backend configuration required");
 const runFetch=config.fetcher??fetch;
 const base=config.supabaseUrl.replace(/\/$/,"");
 return async function saveOwnerAssessment(args:{
   photo:EyePhoto; result:GeminiOwnerResult; model:string; promptVersion:string
 }):Promise<{displayResultId:string}> {
   if (args.photo.id!==args.result.photo_id || !args.promptVersion)
     throw new Error("Assessment photo/version mismatch");
   const data={
     p_photo_id:args.photo.id,p_model:args.model,p_prompt_version:args.promptVersion,
     p_observations:args.result.observations,p_comparison:args.result.comparison,
     p_limitations:args.result.limitations,p_owner_summary:args.result.owner_summary,
     p_actions:args.result.actions,p_display_state:args.result.display_state
   };
   const response=await runFetch(base+"/rest/v1/rpc/save_eye_owner_gemini_assessment",{
     method:"POST",headers:{"apikey":config.serviceKey,
       "Authorization":"Bearer "+config.serviceKey,"Content-Type":"application/json"},
     body:JSON.stringify(data)
   });
   if(!response.ok) throw new Error("Owner assessment transaction failed: "+response.status);
   const id=await response.json();
   if(typeof id!=="string" || !/^[0-9a-f-]{36}$/i.test(id))throw new Error("Invalid persisted display ID");
   return {displayResultId:id};
 };
}
