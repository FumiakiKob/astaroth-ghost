import json, urllib.request, time, sys

# 第3シェル（メイド服）候補生成・方向確認用の試し刷り（各方向1枚）。
# gen_night_candidates2.py のブループリントを踏襲（832x1216 / 30step / CFG4.0 /
# er_sde / simple / 緑一色背景・全身立ち姿・腕は体の横・手は空）。
# M1: アスタロト クラシックメイド（黒x白）
# M2: フルフル ピンクメイド
# M3: フルフル クラシックメイド（黒x白）
# フルフルには gen_v224.py で実績のある頭身指示（PROP_*）を入れる。

ASTA_BASE = (
"masterpiece, best quality, score_7, fallen angel, 1girl, solo, petite, "
"deep purple and violet hair, long hair, wavy hair, choppy bangs, golden amber eyes, "
"round pupils, (pale skin:0.3), gold pendant, halo, "
)
ASTA_PROSE = (
"A petite fallen angel girl standing straight and facing the viewer in a full body shot, "
"her whole body from the top of her halo to the tips of her feet fully visible inside the frame "
"with margin around her, arms relaxed and hanging naturally at her sides, not holding anything, "
"hands empty. "
"Behind her is a completely plain solid bright green background, a single flat uniform green "
"color filling the entire background, chroma key green screen, no scenery, no floor, no shadows, "
"no gradient. Clean silhouette, hair and clothes clearly separated from the green background."
)
asta_m1 = (ASTA_BASE +
"maid, classic maid outfit, black maid dress, white frill apron, lace headdress, maid headdress, "
"white lace trim, long sleeves, puffy shoulders, knee-length dress, white stockings, black mary janes, "
"calm gentle smile, gentle smile, " +
ASTA_PROSE +
" She wears a classic maid outfit, a black maid dress with a white frilled apron over it and a "
"white lace headdress on her head, tasteful and modest, the skirt of the dress falling to around "
"her knees.")
asta_neg = (
"worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
"cropped, out of frame, cut off, upper body only, close-up, scenery, indoors, outdoors, "
"furniture, gradient background, multiple girls, holding book, holding object, sitting, "
"black and gold dress, off-shoulder dress, long dress, gold trim dress, high heels, "
"underwear, bra, panties, lingerie set, excessively revealing, see-through body, "
"nightgown, negligee, pajamas, naked apron"
)

FUR_BASE = (
"masterpiece, best quality, score_7, fallen angel, 1girl, solo, petite, "
"white hair, twintails, hair just past shoulders, curled hair ends, blue eyes, sparkling eyes, "
"round pupils, pinkish skin, blush, cheerful smile, gentle smile, happy, "
"white feather wings, two small white feather wings on her back, "
)
PROP_TAGS = "slender body, long legs, tall proportions, small head, "
PROP_PROSE = ("She has slender, well-balanced proportions with relatively long legs and a smaller head, "
              "about six heads tall, elegant and natural proportions, not chibi. ")
PROP_NEG = ", chibi, super deformed, sd, short legs, stubby legs, large head, big head, toddler proportions, child proportions, dwarf proportions, short body"
FUR_PROSE_TAIL = (
"Two small white feather wings spread slightly behind her back, modest in size, fully visible "
"inside the frame and not too large. She has a cheerful gentle smile, her sparkling blue eyes "
"open and looking at the viewer, bright and energetic. "
"Behind her is a completely plain solid bright green background, a single flat uniform green "
"color filling the entire background, chroma key green screen, no scenery, no floor, no shadows, "
"no gradient. Clean silhouette, hair, wings and clothes clearly separated from the green background."
)
FUR_PROSE_HEAD = (
"A petite fallen angel girl standing straight and facing the viewer in a full body shot, "
"her whole body from the top of her head to the tips of her feet fully visible inside the frame "
"with margin around her, arms relaxed and hanging naturally at her sides, not holding anything, "
"hands empty. "
)

def fur_maid(color_tags, wear_sentence):
    return (FUR_BASE + PROP_TAGS + color_tags + FUR_PROSE_HEAD + wear_sentence + PROP_PROSE + FUR_PROSE_TAIL)

fur_m2 = fur_maid(
    "maid, pink maid dress, pink maid outfit, white frill apron, lace headdress, maid headdress, "
    "white lace trim, puffy short sleeves, knee-length dress, white stockings, pink mary janes, ",
    "She wears a cute pink maid outfit, a pink maid dress with a white frilled apron over it and "
    "a white lace headdress on her head, cheerful and modest, its skirt ending around her knees. ")
fur_m3 = fur_maid(
    "maid, black maid dress, maid outfit, white frill apron, lace headdress, maid headdress, "
    "white lace trim, puffy short sleeves, knee-length dress, white stockings, black mary janes, ",
    "She wears a classic black and white maid outfit, a black maid dress with a white frilled "
    "apron over it and a white lace headdress on her head, cheerful and modest, its skirt ending "
    "around her knees. ")

fur_neg_base = (
"worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
"cropped, out of frame, cut off, upper body only, close-up, scenery, indoors, outdoors, "
"furniture, gradient background, multiple girls, holding book, holding object, sitting, "
"halo, purple hair, black hair, dark hair, black dress, gold dress, long dress, "
"deer, antlers, horns, tail, animal ears, huge wings, giant wings, closed eyes, frown, angry, "
"underwear, bra, panties, lingerie set, excessively revealing"
)
fur_m2_neg = fur_neg_base + ", nightgown, negligee, pajamas" + PROP_NEG
fur_m3_neg = fur_neg_base.replace("black dress, ", "") + ", pink dress, nightgown, negligee, pajamas" + PROP_NEG

JOBS = [
    ("M1", 20261121, asta_m1, asta_neg),
    ("M2", 111701,   fur_m2, fur_m2_neg),
    ("M3", 777701,   fur_m3, fur_m3_neg),
]

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
     "9": {"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":f"maid_{label}_seed{seed}"}}
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
            outs=h[pid].get("outputs",{})
            print("JOB", label, "STATUS", st.get("status_str"), "OUTPUTS", json.dumps(outs), flush=True)
            return 0 if st.get("completed") else 2
    print("JOB", label, "TIMEOUT", flush=True)
    return 3

only = sys.argv[1:] if len(sys.argv) > 1 else None
rc = 0
for label, seed, pos, neg in JOBS:
    if only and label not in only:
        continue
    r = run(label, seed, pos, neg)
    if r != 0:
        rc = r
        print("job failed", label, r, flush=True)
print("DONE rc=", rc)
sys.exit(0)
