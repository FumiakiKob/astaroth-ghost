import json, urllib.request, time, sys

# 第2シェル（夜セット）候補生成。gen_shell.py / gen_furfur.py のブループリント
# （CottonAnima base1、832x1216、30step/CFG4/er_sde、緑背景・全身立ち姿）を踏襲し、
# 衣装だけを夜着に差し替えたもの。採用はユーザーがプレビューで選ぶ。
# A1-A4: アスタロト ネグリジェ（A4のみ薄手ガウン羽織り案）
# P1-P3: フルフル パジャマ
# N1-N3: フルフル 短いネグリジェ

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
"no gradient. Clean silhouette, hair and nightgown clearly separated from the green background."
)
asta_pos_plain = (
ASTA_BASE +
"black silk negligee, deep purple silk nightgown, elegant nightgown with delicate lace trim, "
"knee-length nightgown, thin shoulder straps, bare feet, calm gentle smile, sleepy serene expression, " +
ASTA_PROSE.replace("nightgown clearly", "nightgown clearly") +
" She wears an elegant black and deep purple silk negligee with delicate lace trim along the "
"neckline and hem, tasteful and modest, the skirt of the nightgown falling to around her knees."
)
asta_pos_robe = (
ASTA_BASE +
"black silk negligee, deep purple silk nightgown, elegant nightgown with delicate lace trim, "
"knee-length nightgown, thin shoulder straps, sheer black lace robe worn open over the nightgown, "
"bare feet, calm gentle smile, sleepy serene expression, " +
ASTA_PROSE +
" She wears an elegant black and deep purple silk negligee with delicate lace trim, tasteful "
"and modest, and over it a sheer black lace gown robe worn open, its long sleeves and hem "
"flowing softly."
)
asta_neg = (
"worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
"cropped, out of frame, cut off, upper body only, close-up, scenery, indoors, outdoors, "
"furniture, gradient background, multiple girls, holding book, holding object, sitting, "
"black and gold dress, off-shoulder dress, long dress, gold trim dress, high heels, shoes, "
"underwear, bra, panties, lingerie set, excessively revealing, see-through body"
)

FUR_BASE = (
"masterpiece, best quality, score_7, fallen angel, 1girl, solo, petite, "
"white hair, twintails, hair just past shoulders, curled hair ends, blue eyes, sparkling eyes, "
"round pupils, pinkish skin, blush, cheerful smile, gentle smile, happy, "
"white feather wings, two small white feather wings on her back, "
)
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
fur_pajama_pos = (
FUR_BASE +
"pink pajamas, frilled pajama set, long-sleeved pajama top with white frills and a small ribbon, "
"long pajama pants, fluffy pink slippers, " +
FUR_PROSE_HEAD +
"She wears a cute pink pajama set, a long-sleeved buttoned pajama top with white frills and a "
"small ribbon at the chest, and matching long pajama pants. " +
FUR_PROSE_TAIL
)
fur_negli_pos = (
FUR_BASE +
"short pink babydoll negligee, white and pink silk nightgown, lace trim, frills, "
"nightgown ending above her knees, thin shoulder straps, small ribbon, bare feet, " +
FUR_PROSE_HEAD +
"She wears a cute short pink babydoll negligee with white lace trim and frills, tasteful and "
"modest, its skirt ending above her knees. " +
FUR_PROSE_TAIL
)
fur_neg_base = (
"worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
"cropped, out of frame, cut off, upper body only, close-up, scenery, indoors, outdoors, "
"furniture, gradient background, multiple girls, holding book, holding object, sitting, "
"halo, purple hair, black hair, dark hair, black dress, gold dress, long dress, "
"deer, antlers, horns, tail, animal ears, huge wings, giant wings, closed eyes, frown, angry, "
"underwear, bra, panties, lingerie set, excessively revealing"
)
fur_pajama_neg = fur_neg_base + ", dress, skirt, nightgown, negligee"
fur_negli_neg = fur_neg_base + ", pajamas, long pants, trousers"

JOBS = [
    ("A1", 20261111, asta_pos_plain, asta_neg),
    ("A2", 111101,   asta_pos_plain, asta_neg),
    ("A3", 777101,   asta_pos_plain, asta_neg),
    ("A4", 424201,   asta_pos_robe,  asta_neg),
    ("P1", 20261112, fur_pajama_pos, fur_pajama_neg),
    ("P2", 111201,   fur_pajama_pos, fur_pajama_neg),
    ("P3", 777201,   fur_pajama_pos, fur_pajama_neg),
    ("N1", 20261113, fur_negli_pos,  fur_negli_neg),
    ("N2", 111301,   fur_negli_pos,  fur_negli_neg),
    ("N3", 777301,   fur_negli_pos,  fur_negli_neg),
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
     "9": {"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":f"night_{label}_seed{seed}"}}
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
