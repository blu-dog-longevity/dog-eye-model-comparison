/** Supabase-backed owner workflow dependencies.
 * Draft adapter only: secret values must come from an Edge Function secret manager.
 * All owner authorization occurs using their JWT and existing RLS, before
 * privileged storage access. Do not deploy without integration/security tests.
 */
import type {ImageInput} from "./gemini_owner_backend.ts";
import type {EyePhoto,OwnerDependencies} from "./gemini_owner_workflow.ts";

type Http = typeof fetch;
export function createSupabaseOwnerReadDependencies(args:{
  supabaseUrl:string; publishableKey:string; serviceKey:string; fetcher?:Http;
}): Pick<OwnerDependencies,"getEyePhoto"|"assertCanViewDog"|"loadPrivateImage"|"getPriorSameEye"|"getSanitizedProContext"> & {setOwnerJwt:(token:string)=>void} {
  if (!args.supabaseUrl.startsWith("https://") || !args.publishableKey || !args.serviceKey)
    throw new Error("Missing secure Supabase configuration");
  const fetcher=args.fetcher??fetch, base=args.supabaseUrl.replace(/\/$/,"");
  let ownerJwt="";
  const json=async(url:string,headers:Record<string,string>)=>{
    const r=await fetcher(url,{headers});
    if(!r.ok) throw new Error("Supabase read failed: "+r.status);
    return r.json();
  };
  const asUser=()=>{if(!ownerJwt) throw new Error("Unverified owner token required");return {
    apikey:args.publishableKey,Authorization:"Bearer "+ownerJwt
  };};
  // Instantiate this dependency object afresh for EACH request. Never reuse across users.\n  // Uses user JWT and eye_photos RLS, not elevated service access.
  const photoRow=async(photoId:string):Promise<EyePhoto|null>=>{
    const q=new URLSearchParams({id:"eq."+photoId,select:"id,dog_id,eye_side,storage_bucket,storage_path,captured_at",limit:"1"});
    const rows=await json(base+"/rest/v1/eye_photos?"+q,asUser());
    return rows[0]??null;
  };
  return {
    setOwnerJwt:(token)=>{if(!token)throw new Error("Missing user token");ownerJwt=token;},
    getEyePhoto:photoRow,
    assertCanViewDog:async(jwt,dogId)=>{
      // Verify JWT via Auth endpoint; do not accept a forged dog ID or an arbitrary token.
      if(!jwt || jwt!==ownerJwt)throw new Error("Authenticated token mismatch");
      const auth=await fetcher(base+"/auth/v1/user",{headers:asUser()});
      if(!auth.ok)throw new Error("Authentication invalid");
      // Existing dogs RLS covers ownership and delegated viewing.
      const q=new URLSearchParams({id:"eq."+dogId,select:"id",limit:"1"});
      const rows=await json(base+"/rest/v1/dogs?"+q,asUser());
      if(rows.length!==1)throw new Error("Dog access denied");
    },
    loadPrivateImage:async(bucket,path)=>{
      if(!ownerJwt)throw new Error("Missing authenticated owner context");
      if(!["dog-pro-uploads","dog-media"].includes(bucket))throw new Error("Unsupported private bucket");
      if(!path||path.startsWith("/")||path.split("/").some(s=>!s||s==="."||s===".."))throw new Error("Invalid private storage path");
      const objectPath=path.split("/").map(encodeURIComponent).join("/");
      const r=await fetcher(base+"/storage/v1/object/"+encodeURIComponent(bucket)+"/"+objectPath,{
        headers:{apikey:args.serviceKey,Authorization:"Bearer "+args.serviceKey}
      });
      if(!r.ok)throw new Error("Private photograph unavailable");
      const type=(r.headers.get("content-type")??"").split(";")[0];
      if(!["image/jpeg","image/png","image/webp"].includes(type))throw new Error("Unsupported image media type");
      const bytes=new Uint8Array(await r.arrayBuffer());
      if(bytes.length>8*1024*1024||bytes.length<20)throw new Error("Unsupported image size");
      // Deno-compatible conversion; not a browser-visible URL.
      let binary="";for(const byte of bytes)binary+=String.fromCharCode(byte);
      return {mimeType:type as ImageInput["mimeType"],base64:btoa(binary)};
    },
    getPriorSameEye:async(dogId,side,beforePhotoId)=>{
      const current=await photoRow(beforePhotoId);
      if(!current||current.dog_id!==dogId||current.eye_side!==side)return null;
      const q=new URLSearchParams({
        dog_id:"eq."+dogId, eye_side:"eq."+side,id:"neq."+beforePhotoId,

        select:"id,dog_id,eye_side,storage_bucket,storage_path,captured_at",
        order:"submitted_at.desc",limit:"10"
      });
      const rows=await json(base+"/rest/v1/eye_photos?"+q,asUser());
      return rows[0]??null;
    },
    getSanitizedProContext:async()=>({symptoms:[],interventions:[],vetFindings:[]}),
  };
}
