import json, urllib.request, time, sys

# Maid Furfur 13-15 wing-size fix: same seeds (777701), same expressions as
# gen_maid_expr.py, with reinforced small-wing specification.
# (v2.23 precedent: one regeneration pass for wing deviation.)

FUR_BASE = (
    "masterpiece, best quality, score_7, fallen angel, 1girl, solo, petite, "
    "white hair, twintails, hair just past shoulders, curled hair ends, blue eyes, sparkling eyes, "
    "round pupils, pinkish skin, blush, "
    "white feather wings, two very small white feather wings on her back, tiny wings, "
)
PROP_TAGS = "slender body, long legs, tall proportions, small head, "
PROP_PROSE = ("She has slender, well-balanced proportions with relatively long legs and a smaller head, "
              "about six heads tall, elegant and natural proportions, not chibi. ")
PROP_NEG = ", chibi, super deformed, sd, short legs, stubby legs, large head, big head, toddler proportions, child proportions, dwarf proportions, short body"
FUR_OUTFIT = (
    "maid, black maid dress, maid outfit, white frill apron, lace headdress, maid headdress, "
    "white lace trim, puffy short sleeves, knee-length dress, white stockings, black mary janes, "
)
FUR_HEAD = (
    "A petite fallen angel girl standing straight and facing the viewer in a full body shot, "
    "her whole body from the top of her head to the tips of her feet fully visible inside the frame "
    "with margin around her, arms relaxed and hanging naturally at her sides, not holding anything, "
    "hands empty. "
)
FUR_WEAR = (
    "She wears a classic black and white maid outfit, a black maid dress with a white frilled "
    "apron over it and a white lace headdress on her head, cheerful and modest, its skirt ending "
    "around her knees. "
)
FUR_WINGS = (
    "Two very small white feather wings tucked closely behind her shoulders, small and modest "
    "in size, close to her back and not spread out, fully visible inside the frame. "
)
FUR_BG = (
    "Behind her is a completely plain solid bright green background, a single flat uniform green "
    "color filling the entire background, chroma key green screen, no scenery, no floor, no shadows, "
    "no gradient. Clean silhouette, hair, wings and clothes clearly separated from the green background."
)
FUR_NEG_BASE = (
    "worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "cropped, out of frame, cut off, upper body only, close-up, scenery, indoors, outdoors, "
    "furniture, gradient background, multiple girls, holding book, holding object, sitting, "
    "halo, purple hair, black hair, dark hair, gold dress, long dress, "
    "deer, antlers, horns, tail, animal ears, huge wings, giant wings, "
    "underwear, bra, panties, lingerie set, excessively revealing"
)
FUR_NEG = FUR_NEG_BASE + ", pink dress, nightgown, negligee, pajamas, large wings, wide wings, spread wings, long wings, wings spread wide" + PROP_NEG
FUR_EYES = "blue eyes, sparkling eyes, round pupils, "
FUR_EXPRS = {
    13: {
        "tags": FUR_EYES + "pout, puffed cheeks, sulky, annoyed, furrowed brows, frown, looking to the side, ",
        "prose": "She is sulking and pouting, her cheeks slightly puffed, her eyebrows furrowed in annoyance, her mouth in a small displeased pout, glancing to the side. ",
        "neg": ", smile, happy, blush, wide eyes, open mouth",
    },
    14: {
        "tags": FUR_EYES + "blush, deep blush, red cheeks, embarrassed, shy, in love, small bashful smile, looking to the side, averted gaze, ",
        "prose": "She is deeply embarrassed and lovestruck, her cheeks blushing bright pink, her gaze turned slightly to the side away from the viewer, with a small bashful happy smile. ",
        "neg": ", looking at viewer, angry, frown, calm expression",
    },
    15: {
        "tags": "closed eyes, serene expression, gentle smile, sleepy, content, ",
        "prose": "Her eyes are gently closed, with a calm serene and content expression and a soft peaceful smile, as if satisfied and a little sleepy. ",
        "neg": ", open eyes, looking at viewer, frown, angry",
    },
}

JOBS = []
for n, e in FUR_EXPRS.items():
    pos = FUR_BASE + PROP_TAGS + FUR_OUTFIT + e["tags"] + FUR_HEAD + FUR_WEAR + PROP_PROSE + FUR_WINGS + e["prose"] + FUR_BG
    JOBS.append((f"MF{n}", 777701, pos, FUR_NEG + e["neg"]))

def run(label, seed, positive, negative):
    workflow = {
     "1": {"class_type":"UNETLoader","inputs":{"unet_name":"cottonanima_base1.safetensors","weight_dtype":"default"}},
     "2": {"class_type":"CLIPLoader","inputs":{"clip_name":"qwen_3_06b_base.safetensors","type":"stable_diffusion","device":"default"}},
     "3": {"class_type":"VAELoader","inputs":{"vae_name":"qwen_image_vae.safetensors"}},
     "4": {"class_type":"CLIPTextEncode","inputs":{"clip":["2",0],"text":positive}},
     "5": {"class_type":"CLIPTextEncode","inputs":{"clip":["2",0],"text":negative}},
     "6": {"class_type":"EmptyLatentImage","inputs":{"width":832,"height":1216,"batch_size":1}},
     "7": {"class_type":"KSampler","inputs":{"model":["1",0],"seed":seed,"steps":30,"cfg":4.0,"sampler_name":"er_sde","scheduler":"simple","positive":["4",0],"negative":["5",0],"latent_image":["6",0],"denoise":1.0}},
     "8": {"class_type":"VAEDecode","inputs":{"samples":["7",0],"vae":["3",0]}},
     "9": {"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":f"maid_fix_{label}_seed{seed}"}}
    }
    data=json.dumps({"prompt":workflow}).encode()
    req=urllib.request.Request("http://127.0.0.1:8188/prompt", data=data, headers={"Content-Type":"application/json"})
    resp=json.loads(urllib.request.urlopen(req, timeout=30).read())
    pid=resp["prompt_id"]
    print("JOB", label, "SEED", seed, "PROMPT_ID", pid, flush=True)
    for i in range(120):
        time.sleep(5)
        h=json.loads(urllib.request.urlopen(f"http://127.0.0.1:8188/history/{pid}", timeout=15).read())
        if pid in h:
            st=h[pid].get("status",{})
            print("JOB", label, "STATUS", st.get("status_str"), flush=True)
            return 0 if st.get("completed") else 2
    print("JOB", label, "TIMEOUT", flush=True)
    return 3

rc = 0
for label, seed, pos, neg in JOBS:
    r = run(label, seed, pos, neg)
    if r != 0:
        rc = r
        print("job failed", label, r, flush=True)
print("DONE rc=", rc)
sys.exit(rc)
