/**
 * Gemini owner-analysis adapter for a trusted server runtime (Deno/Edge).
 * Not deployed. Never call this from a browser.
 *
 * Caller MUST: verify JWT and can_view_dog / can_edit_dog, fetch the verified
 * private image bytes using server credentials, enforce rate/size limits, and
 * save versioned run and assessment records transactionally.
 */
export type ImageInput = { mimeType: "image/jpeg" | "image/png" | "image/webp"; base64: string };
export type EyeContext = {
  photoId: string; eyeSide: "left" | "right"; ageYears?: number;
  priorSameEye?: { photoId: string; capturedAt: string; image: ImageInput };
  proSummary: { symptoms: unknown[]; interventions: unknown[]; vetFindings: unknown[] };
};
export type GeminiOwnerResult = {
  photo_id: string;
  observations: Record<string, { severity: "none" | "mild" | "moderate" | "severe" | "unclear"; description: string }>;
  display_state: "ready" | "needs_review" | "unavailable";
  owner_summary: string;
  comparison: { change: "increased" | "decreased" | "no_clear_change" | "unable_to_compare"; previous_photo_id: string | null };
  limitations: string[];
  actions: string[];
};
export const OBS_KEYS = ["cloudiness","redness","discharge","swelling","iris_appearance","pupil_appearance","third_eyelid","eyelids","eye_surface"] as const;
const SEVERITY = ["none","mild","moderate","severe","unclear"];
const CHANGES = ["increased","decreased","no_clear_change","unable_to_compare"];
export function validateOwnerResult(value: unknown, photoId: string, expectedPreviousPhotoId?: string): GeminiOwnerResult {
  if (!value || typeof value !== "object") throw new Error("Malformed Gemini response");
  const x = value as Record<string, unknown>;
  if (x.photo_id !== photoId || !x.observations || typeof x.observations !== "object") throw new Error("Photo/reference mismatch");
  const obs = x.observations as Record<string, unknown>;
  if (Object.keys(obs).sort().join("|") !== [...OBS_KEYS].sort().join("|")) throw new Error("Incomplete observations");
  for (const key of OBS_KEYS) {
    const item = obs[key] as Record<string, unknown> | null;
    if (!item || !SEVERITY.includes(String(item.severity)) || typeof item.description !== "string") throw new Error("Invalid observation");
  }
  if (!["ready","needs_review","unavailable"].includes(String(x.display_state))) throw new Error("Invalid display state");
  if (typeof x.owner_summary !== "string" || !x.owner_summary.trim()) throw new Error("Missing summary");
  if (!Array.isArray(x.limitations) || !x.limitations.every(v=>typeof v==="string")) throw new Error("Invalid limitations");
  if (!Array.isArray(x.actions) || !x.actions.every(v=>typeof v==="string")) throw new Error("Invalid actions");
  if (x.diagnosis != null || x.clinical_accuracy_verified === true) throw new Error("Unsupported diagnosis claim");
  const comparison = x.comparison as Record<string, unknown> | null;
  if (!comparison || !CHANGES.includes(String(comparison.change))) throw new Error("Invalid comparison");
  if (comparison.previous_photo_id !== (expectedPreviousPhotoId ?? null)) throw new Error("Prior-photo mismatch");
  if (comparison.change !== "unable_to_compare" && !expectedPreviousPhotoId) throw new Error("Unsupported change");
  return x as unknown as GeminiOwnerResult;
}
export function buildGeminiRequest(photo: ImageInput, ctx: EyeContext, model: string) {
  if (!/^gemini-[a-z0-9.-]+$/.test(model)) throw new Error("Model identifier must be configured by backend");
  if (!photo.base64 || !ctx.photoId) throw new Error("Missing photo");
  const parts: unknown[] = [
    { text: [
      "You are analyzing a dog eye photo for visual observations, not diagnosis.",
      "Never claim to confirm cataracts, glaucoma, other conditions or medical accuracy.",
      "If image quality is uncertain use needs_review and explain uncertainty.",
      "Describe visible signs, compare only the supplied same-eye earlier photo if present.",
      "Do not infer treatment effectiveness from reported timing.",
      "Urgent painful squinting, sudden vision loss, serious injury: advise prompt veterinary evaluation.",
      "Return ONLY JSON with keys photo_id, observations (exact: "+OBS_KEYS.join(", ")+"), display_state, owner_summary, comparison, limitations, actions.",
      "Each observation is {severity: none|mild|moderate|severe|unclear, description: string}.",
      "Comparison is {change: increased|decreased|no_clear_change|unable_to_compare, previous_photo_id: string|null}.",
      "Use photo_id exactly "+ctx.photoId+" and previous_photo_id exactly "+(ctx.priorSameEye?.photoId ?? "null")+".",
      "Context is owner-reported, not vetted fact: "+JSON.stringify({eyeSide:ctx.eyeSide,ageYears:ctx.ageYears,proSummary:ctx.proSummary}).slice(0,16000),
    ].join("\n") },
    { inlineData: {mimeType: photo.mimeType, data:photo.base64} },
  ];
  if (ctx.priorSameEye) parts.push({text:"Previous photo of the SAME eye, dated "+ctx.priorSameEye.capturedAt},{inlineData:{mimeType:ctx.priorSameEye.image.mimeType,data:ctx.priorSameEye.image.base64}});
  return { model, contents:[{role:"user",parts}],generationConfig:{responseMimeType:"application/json",temperature:0.1}};
}
export async function callGeminiOwner(photo: ImageInput, ctx: EyeContext, options: {apiKey:string;model:string;fetcher?:typeof fetch}):Promise<GeminiOwnerResult> {
  if (!options.apiKey) throw new Error("Missing server-side Gemini API key");
  const body=buildGeminiRequest(photo,ctx,options.model);
  const endpoint="https://generativelanguage.googleapis.com/v1beta/models/"+encodeURIComponent(options.model)+":generateContent";
  const response=await (options.fetcher??fetch)(endpoint,{method:"POST",headers:{"Content-Type":"application/json","x-goog-api-key":options.apiKey},body:JSON.stringify({contents:body.contents,generationConfig:body.generationConfig})});
  if (!response.ok) throw new Error("Gemini API request failed: "+response.status);
  const raw=await response.json();
  const text=raw?.candidates?.[0]?.content?.parts?.find((p: {text?:string})=>typeof p.text==="string")?.text;
  if (!text) throw new Error("Missing Gemini response text");
  let parsed:unknown;
  try {parsed=JSON.parse(text);} catch {throw new Error("Gemini returned malformed JSON");}
  return validateOwnerResult(parsed,ctx.photoId,ctx.priorSameEye?.photoId);
}
