import json, urllib.request, time, sys

# 第2シェル（夜セット）候補生成・第2便。gen_night_candidates.py のブループリントを
# 踏襲し、色で普段着と明確に差をつけることが目的。
# A5-A8: アスタロト ネグリジェ別色（アイボリー／ワインレッド／ラベンダーブルー／エメラルド）
# P4-P6: フルフル パジャマ別色（水色／ミント／ラベンダー、夜モチーフ柄）
# N4-N6: フルフル 短いネグリジェ別色（白／黒／水色、ピンクを外す）

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

def asta_pos(color_tags, tail):
    return (ASTA_BASE + color_tags +
            "bare feet, calm gentle smile, sleepy serene expression, " +
            ASTA_PROSE + tail)

asta_a5 = asta_pos(
    "white silk negligee, ivory white silk nightgown, elegant nightgown with delicate white lace trim, "
    "knee-length nightgown, thin shoulder straps, ",
    " She wears an elegant ivory white silk negligee with delicate white lace trim along the "
    "neckline and hem, tasteful and modest, the skirt of the nightgown falling to around her knees.")
asta_a6 = asta_pos(
    "wine red silk negligee, deep red silk nightgown, elegant nightgown with delicate black lace trim, "
    "short nightgown ending above the knees, thin shoulder straps, ",
    " She wears an elegant wine red silk negligee with delicate black lace trim along the "
    "neckline and hem, tasteful and modest, the skirt of the nightgown ending above her knees.")
asta_a7 = asta_pos(
    "pale lavender blue silk negligee, light blue-violet silk nightgown, elegant nightgown with delicate white lace trim, "
    "long nightgown falling below the knees, thin shoulder straps, sheer lavender robe worn open over the nightgown, ",
    " She wears an elegant pale lavender blue silk negligee with delicate white lace trim, tasteful "
    "and modest, the skirt of the nightgown falling below her knees, and over it a sheer lavender "
    "robe worn open, its sleeves and hem flowing softly.")
asta_a8 = asta_pos(
    "emerald green silk negligee, deep green silk nightgown, elegant nightgown with delicate gold lace trim, "
    "knee-length nightgown, thin shoulder straps, ",
    " She wears an elegant emerald green silk negligee with delicate lace trim along the "
    "neckline and hem, tasteful and modest, the skirt of the nightgown falling to around her knees.")

asta_neg = (
"worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
"cropped, out of frame, cut off, upper body only, close-up, scenery, indoors, outdoors, "
"furniture, gradient background, multiple girls, holding book, holding object, sitting, "
"black and gold dress, off-shoulder dress, long dress, gold trim dress, high heels, shoes, "
"underwear, bra, panties, lingerie set, excessively revealing, see-through body, "
"black negligee, black nightgown"
)
asta_neg_purple = asta_neg + ", deep purple nightgown, purple nightgown"

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

def fur_pajama(color_tags, wear_sentence):
    return (FUR_BASE + color_tags + FUR_PROSE_HEAD + wear_sentence + FUR_PROSE_TAIL)

fur_p4 = fur_pajama(
    "light blue pajamas, star and crescent moon pattern pajamas, long-sleeved pajama top with white frills and a small ribbon, "
    "long pajama pants, fluffy light blue slippers, ",
    "She wears a cute light blue pajama set printed with small white stars and crescent moons, "
    "a long-sleeved buttoned pajama top with white frills and a small ribbon at the chest, and "
    "matching long pajama pants. ")
fur_p5 = fur_pajama(
    "mint green pajamas, star pattern pajamas, long-sleeved pajama top with white frills and a small ribbon, "
    "long pajama pants, fluffy mint green slippers, ",
    "She wears a cute mint green pajama set printed with small white stars, a long-sleeved "
    "buttoned pajama top with white frills and a small ribbon at the chest, and matching long "
    "pajama pants. ")
fur_p6 = fur_pajama(
    "lavender pajamas, crescent moon pattern pajamas, long-sleeved pajama top with white frills and a small ribbon, "
    "long pajama pants, fluffy lavender slippers, ",
    "She wears a cute lavender pajama set printed with small white crescent moons, a long-sleeved "
    "buttoned pajama top with white frills and a small ribbon at the chest, and matching long "
    "pajama pants. ")

def fur_negli(color_tags, wear_sentence):
    return (FUR_BASE + color_tags + FUR_PROSE_HEAD + wear_sentence + FUR_PROSE_TAIL)

fur_n4 = fur_negli(
    "short white babydoll negligee, white silk nightgown, white lace trim, frills, "
    "nightgown ending above her knees, thin shoulder straps, small pink ribbon, pink ribbon accents, bare feet, ",
    "She wears a cute short white babydoll negligee with white lace trim and frills and small "
    "pink ribbon accents, tasteful and modest, its skirt ending above her knees. ")
fur_n5 = fur_negli(
    "short black babydoll negligee, black silk nightgown, white lace trim, frills, "
    "nightgown ending above her knees, thin shoulder straps, small white ribbon, bare feet, ",
    "She wears a cute short black babydoll negligee with white lace trim and frills, tasteful "
    "and modest, its skirt ending above her knees. ")
fur_n6 = fur_negli(
    "short light blue babydoll negligee, light blue silk nightgown, white lace trim, frills, "
    "nightgown ending above her knees, thin shoulder straps, small white ribbon, bare feet, ",
    "She wears a cute short light blue babydoll negligee with white lace trim and frills, "
    "tasteful and modest, its skirt ending above her knees. ")

fur_neg_base = (
"worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
"cropped, out of frame, cut off, upper body only, close-up, scenery, indoors, outdoors, "
"furniture, gradient background, multiple girls, holding book, holding object, sitting, "
"halo, purple hair, black hair, dark hair, black dress, gold dress, long dress, "
"deer, antlers, horns, tail, animal ears, huge wings, giant wings, closed eyes, frown, angry, "
"underwear, bra, panties, lingerie set, excessively revealing"
)
fur_pajama_neg = fur_neg_base + ", dress, skirt, nightgown, negligee, pink pajamas"
fur_negli_neg = fur_neg_base + ", pajamas, long pants, trousers, pink dress"
fur_n4_neg = fur_negli_neg
fur_n5_neg = fur_neg_base.replace("black dress, ", "") + ", pajamas, long pants, trousers, pink dress, pink negligee, pink nightgown"
fur_n6_neg = fur_negli_neg + ", pink negligee, pink nightgown"

JOBS = [
    ("A5", 20261211, asta_a5, asta_neg_purple),
    ("A6", 121201,   asta_a6, asta_neg_purple),
    ("A7", 777401,   asta_a7, asta_neg),
    ("A8", 424501,   asta_a8, asta_neg_purple),
    ("P4", 20261212, fur_p4, fur_pajama_neg),
    ("P5", 121501,   fur_p5, fur_pajama_neg),
    ("P6", 777501,   fur_p6, fur_pajama_neg),
    ("N4", 20261213, fur_n4, fur_n4_neg),
    ("N5", 121601,   fur_n5, fur_n5_neg),
    ("N6", 777601,   fur_n6, fur_n6_neg),
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
