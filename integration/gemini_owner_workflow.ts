/** Server-only Gemini owner workflow. No deployment or network side effects on import.
 * Host must provide authenticated identity, scoped photo retrieval, private image
 * bytes, clinical context, and an atomic versioned persistence implementation.
 */
import {callGeminiOwner, type ImageInput, type EyeContext, type GeminiOwnerResult} from "./gemini_owner_backend.ts";
export type EyePhoto = { id:string; dog_id:string; eye_side:"left"|"right"; storage_bucket:string; storage_path:string; captured_at:string|null };
export type OwnerDependencies = {
  /** Must use verified JWT / dog access rules; do not authorize from client dog_id alone. */
  assertCanViewDog:(userJwt:string,dogId:string)=>Promise<void>;
  getEyePhoto:(photoId:string)=>Promise<EyePhoto|null>;
  /** No arbitrary URLs; storage path is read from authorized DB row only. */
  loadPrivateImage:(bucket:string,path:string)=>Promise<ImageInput>;
  getPriorSameEye:(dogId:string,eyeSide:"left"|"right",beforePhotoId:string)=>Promise<EyePhoto|null>;
  getSanitizedProContext:(dogId:string)=>Promise<EyeContext["proSummary"]>;
  /** Single trusted transaction: create Gemini owner model run, assessment, immutable display snapshot.
   * Must be idempotent by (photoId, promptVersion, runKind='owner').
   * Must enforce same dog/photo references and disallow public client inserts.
   */
  saveOwnerAssessment:(args:{photo:EyePhoto;result:GeminiOwnerResult;model:string;promptVersion:string})=>Promise<{displayResultId:string}>;
  callGemini?:typeof callGeminiOwner;
};
export type OwnerConfig={model:string;promptVersion:string;geminiApiKey:string;maxImageBytes:number};
function estimateBytes(image:ImageInput):number {return Math.floor(image.base64.length*3/4);}
function guardImage(image:ImageInput,maxBytes:number):void {
  if (!image.base64 || estimateBytes(image)>maxBytes || estimateBytes(image)<20) throw new Error("Unsupported image size");
  if (!["image/jpeg","image/png","image/webp"].includes(image.mimeType)) throw new Error("Unsupported media type");
}
export async function assessOwnerEye(input:{userJwt:string;photoId:string}, deps:OwnerDependencies, cfg:OwnerConfig):Promise<{displayResultId:string}> {
  if (!input.userJwt || !input.photoId) throw new Error("Authentication and photo ID required");
  if (!cfg.geminiApiKey || !cfg.promptVersion || !cfg.model) throw new Error("Missing backend configuration");
  const photo=await deps.getEyePhoto(input.photoId);
  if (!photo || photo.eye_side==="unknown") throw new Error("Photo not eligible for analysis");
  await deps.assertCanViewDog(input.userJwt,photo.dog_id);
  // Authorization occurs BEFORE fetching sensitive image bytes or dog history.
  const image=await deps.loadPrivateImage(photo.storage_bucket,photo.storage_path);
  guardImage(image,cfg.maxImageBytes);
  const previous=await deps.getPriorSameEye(photo.dog_id,photo.eye_side,photo.id);
  if (previous && (previous.dog_id!==photo.dog_id || previous.eye_side!==photo.eye_side || previous.id===photo.id))
    throw new Error("Historical photo mismatch");
  const priorImage=previous?await deps.loadPrivateImage(previous.storage_bucket,previous.storage_path):undefined;
  if (priorImage) guardImage(priorImage,cfg.maxImageBytes);
  const ctx:EyeContext={
    photoId:photo.id,eyeSide:photo.eye_side,
    proSummary:await deps.getSanitizedProContext(photo.dog_id),
    ...(previous&&priorImage?{priorSameEye:{photoId:previous.id,capturedAt:previous.captured_at??"",image:priorImage}}:{})
  };
  const result=await (deps.callGemini??callGeminiOwner)(image,ctx,{apiKey:cfg.geminiApiKey,model:cfg.model});
  return deps.saveOwnerAssessment({photo,result,model:cfg.model,promptVersion:cfg.promptVersion});
}
