import json, urllib.request, time, sys

# v2.27 生成一括スクリプト: 第3シェル「maid」の仮置き差し替え。
# アスタロト ポーズ6-9/46-49、フルフル ポーズ16-19/56-59、座り20/21（全18面）。
# ポーズの構図・意味づけ・表情対応は gen_v223.py（夜シェル量産）から移植し、
# 衣装ブロックと土台シードは gen_maid_expr.py（maid 基本面量産）に合わせる：
#   アスタロト = M1（seed 20261121、クラシックメイド黒×白）
#   フルフル   = M3（seed 777701、クラシックメイド黒×白、頭身指示つき）
# 表情違いは土台ポーズと同一シード（maid 基本面量産の流儀）。
# usage: gen_maid_poses.py [label ...]  （無指定で全件。WSL 上で実行する）

PROP_TAGS = "slender body, long legs, tall proportions, small head, "
PROP_PROSE = ("She has slender, well-balanced proportions with relatively long legs and a smaller head, "
              "about six heads tall, elegant and natural proportions, not chibi. ")
PROP_NEG = ", chibi, super deformed, sd, short legs, stubby legs, large head, big head, toddler proportions, child proportions, dwarf proportions, short body"
FRAME = ("A petite fallen angel girl in a full body shot, her whole body from the top of her head to the tips "
         "of her feet fully visible inside the frame with margin around her, ")
HAND_NEG = ", oversized hands, huge hands, big hands, disproportionate hands, long fingers"
SYMBOL_NEG = ", floating symbols, steam puffs, emphasis lines, motion lines, sparkles"

# ---------- アスタロト M1（gen_maid_expr.py と同一ブロック） ----------
A_BASE = ("masterpiece, best quality, score_7, fallen angel, 1girl, solo, petite, "
          "deep purple and violet hair, long hair, wavy hair, choppy bangs, golden amber eyes, "
          "round pupils, (pale skin:0.3), gold pendant, halo, ")
A_OUTFIT = ("maid, classic maid outfit, black maid dress, white frill apron, lace headdress, "
            "maid headdress, white lace trim, long sleeves, puffy shoulders, knee-length dress, "
            "white stockings, black mary janes, ")
A_BG = ("Behind her is a completely plain solid bright green background, a single flat uniform green "
        "color filling the entire background, chroma key green screen, no scenery, no floor, no shadows, "
        "no gradient. Clean silhouette, hair and clothes clearly separated from the green background.")
A_TAIL = (" She wears a classic maid outfit, a black maid dress with a white frilled apron over it and a "
          "white lace headdress on her head, tasteful and modest, the skirt of the dress falling to around "
          "her knees.")
A_NEG = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
         "cropped, out of frame, cut off, upper body only, close-up, scenery, indoors, outdoors, "
         "furniture, gradient background, multiple girls, holding book, holding object, sitting, "
         "black and gold dress, off-shoulder dress, long dress, gold trim dress, high heels, "
         "underwear, bra, panties, lingerie set, excessively revealing, see-through body, "
         "nightgown, negligee, pajamas, naked apron")
A_CALM = "She has a calm gentle expression, her golden eyes looking softly at the viewer. "
A_FRAME = ("A petite fallen angel girl in a full body shot, her whole body from the top of her halo to the tips "
           "of her feet fully visible inside the frame with margin around her, ")
A_SEED = 20261121

# ポーズ定義は gen_v223.py の A_POSES / A_POSE_EXPR と同一（シードは M1 に統一）
A_POSES = {
    6: ("standing, own hands together, hands clasped in front, ",
        A_FRAME + "standing straight and facing the viewer, her arms lowered in front of her body with both hands gently clasped together in front of her waist, a calm docile standing posture, not holding anything. ",
        A_CALM),
    7: ("three-quarter view, own hands together, hands clasped in front of chest, head bowed, worried expression, ",
        A_FRAME + "shown in a three-quarter view with her body turned slightly to the side, both hands clasped together in front of her chest, her head slightly bowed, not holding anything. ",
        "She has a gentle worried expression, her eyebrows slightly raised in concern, gazing quietly toward the viewer. "),
    8: ("holding book, book, old book, ",
        A_FRAME + "standing straight and facing the viewer, hugging a thick old leather-bound book against her chest with both arms. ",
        A_CALM),
    9: ("arms crossed, crossed arms, looking down, confident, ",
        A_FRAME + "standing straight and facing the viewer, her arms firmly crossed over her chest, her chin slightly raised in a confident posture, not holding anything. ",
        "She looks slightly down at the viewer with a composed, mildly condescending, unimpressed expression. "),
}
A_POSE_EXPR = {
    46: (6, "gentle smile, warm smile, happy, ",
         "She has a gentle warm smile, her golden eyes open and looking softly at the viewer, a kind and happy expression. ",
         ", frown, angry, closed eyes"),
    47: (7, "closed eyes, serene expression, gentle smile, ",
         "Her eyes are gently closed, with a calm serene expression and a soft peaceful smile, her head still slightly bowed. ",
         ", open eyes, looking at viewer, frown"),
    48: (8, "gentle smile, warm smile, happy, ",
         "She has a gentle warm smile, her golden eyes open and looking softly at the viewer, a kind and happy expression. ",
         ", frown, angry, closed eyes"),
    49: (9, "",
         A_CALM, ", angry, frown"),
}

# ---------- フルフル M3（gen_maid_expr.py と同一ブロック） ----------
F_BASE = ("masterpiece, best quality, score_7, fallen angel, 1girl, solo, petite, "
          "white hair, twintails, hair just past shoulders, curled hair ends, blue eyes, sparkling eyes, "
          "round pupils, pinkish skin, blush, "
          "white feather wings, two small white feather wings on her back, ")
F_OUTFIT = ("maid, black maid dress, maid outfit, white frill apron, lace headdress, maid headdress, "
            "white lace trim, puffy short sleeves, knee-length dress, white stockings, black mary janes, ")
F_WEAR = ("She wears a classic black and white maid outfit, a black maid dress with a white frilled "
          "apron over it and a white lace headdress on her head, cheerful and modest, its skirt ending "
          "around her knees. ")
F_WINGS = ("Two small white feather wings spread slightly behind her back, modest in size, fully visible "
           "inside the frame and not too large. ")
F_BG = ("Behind her is a completely plain solid bright green background, a single flat uniform green "
        "color filling the entire background, chroma key green screen, no scenery, no floor, no shadows, "
        "no gradient. Clean silhouette, hair, wings and clothes clearly separated from the green background.")
F_NEG_BASE = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
              "cropped, out of frame, cut off, upper body only, close-up, scenery, indoors, outdoors, "
              "furniture, gradient background, multiple girls, holding book, holding object, sitting, "
              "halo, purple hair, black hair, dark hair, gold dress, long dress, "
              "deer, antlers, horns, tail, animal ears, huge wings, giant wings, "
              "underwear, bra, panties, lingerie set, excessively revealing")
F_NEG = F_NEG_BASE + ", pink dress, nightgown, negligee, pajamas" + PROP_NEG
F_EYES = "blue eyes, sparkling eyes, round pupils, "
F_SEED = 777701

# ポーズ定義は gen_v223.py の F_POSES / F_POSE_EXPR を移植（目のタグは maid 基本面に合わせ F_EYES を使用）
F_POSES = {
    16: ("leaning forward, bending forward, reaching out, arms reaching toward viewer, open hands, excited, happy, open mouth smile, :d, " + F_EYES,
         "leaning forward toward the viewer with her upper body tilted in eagerly, both arms stretched out toward the viewer with open palms as if reaching out to grab or hug the viewer, an eager pushy posture full of energy. ",
         "She has an eager excited expression, sparkling eyes and a big happy open-mouth smile, thrilled to get closer. ",
         HAND_NEG + ", standing straight, arms hanging at sides, calm expression, frown"),
    17: ("arms spread wide, arms outstretched to the sides, joyful, happy, open mouth smile, :d, " + F_EYES,
         "standing straight and facing the viewer with both arms spread wide open to her sides in delight, her two white feather wings also spread wide behind her shoulders, a joyful welcoming posture. ",
         "She has a bright joyful expression with a big happy open-mouth smile, beaming with delight. ",
         ", arms hanging at sides, folded wings, closed eyes, calm expression, frown"),
    18: ("from behind, back view, three-quarter back view, looking back, looking over shoulder, arms crossed, pout, puffed cheeks, sulky, annoyed, furrowed brows, ",
         "shown from a three-quarter back view with her body turned away from the viewer in a sulk, her arms crossed over her chest, her head turned to look back over her shoulder at the viewer, her white feather wings visible from behind her shoulders. ",
         "She is sulking and pouting, her cheeks puffed, her eyebrows furrowed in annoyance, her mouth in a small displeased pout as she glares back over her shoulder with sparkling blue eyes. ",
         ", body facing viewer, full front view, smile, happy, joyful, open mouth smile"),
    19: ("hands clasped, own hands together, hands clasped in front of chest, begging, pleading, upward gaze, looking up, " + F_EYES,
         "standing straight and facing the viewer, both hands clasped together tightly in front of her chest in a begging gesture, leaning very slightly forward, not holding anything. ",
         "She looks up at the viewer with a pleading upward gaze, her starry eyes sparkling hopefully, her mouth in a small hopeful smile, earnestly begging for a favor. ",
         ", arms hanging at sides, looking down, angry, frown, closed eyes"),
}
F_POSE_EXPR = {
    56: (16, F_EYES + "blush, deep blush, red cheeks, embarrassed, shy, in love, bashful smile, ",
         "She is deeply embarrassed and lovestruck even as she leans in close, her cheeks blushing bright pink, with a small bashful happy smile, her gaze eager but shy. ",
         HAND_NEG + ", standing straight, arms hanging at sides, calm expression, angry, frown, closed eyes"),
    57: (17, "closed eyes, blissful, content, gentle smile, satisfied, ",
         "Her eyes are gently closed in pure bliss, with a satisfied content smile, savoring the happy moment. ",
         ", arms hanging at sides, folded wings, open eyes, looking at viewer, frown"),
    58: (18, "surprised, wide eyes, raised eyebrows, open mouth, :o, ",
         "She looks genuinely surprised as she glances back over her shoulder, her sparkling blue eyes wide open, her eyebrows raised, her mouth open in a small round shape, caught off guard. ",
         SYMBOL_NEG + ", body facing viewer, full front view, closed eyes, calm expression, smile, pout, puffed cheeks"),
    59: (19, F_EYES + "big smile, open mouth smile, :d, very happy, joyful, ",
         "She has a big joyful open-mouth smile, beaming happily up at the viewer as she begs, full of energy and delight, her starry eyes sparkling. ",
         ", arms hanging at sides, looking down, angry, frown, closed eyes, sad, small smile"),
}

JOBS = []  # (label, seed, positive, negative)

def asta_pose(surf):
    tags, prose, expr = A_POSES[surf]
    neg = A_NEG
    if surf == 8:
        neg = neg.replace("holding book, holding object, ", "")
    pos = A_BASE + A_OUTFIT + tags + prose + expr + A_BG + A_TAIL
    return (f"MA{surf}", A_SEED, pos, neg)

def asta_pose_expr(surf):
    base, etags, eprose, eneg = A_POSE_EXPR[surf]
    tags, prose, _expr = A_POSES[base]
    neg = A_NEG
    if base == 8:
        neg = neg.replace("holding book, holding object, ", "")
    pos = A_BASE + A_OUTFIT + tags + etags + prose + eprose + A_BG + A_TAIL
    return (f"MA{surf}", A_SEED, pos, neg + eneg)

def asta_sit():
    pos = (A_BASE + A_OUTFIT
           + "sitting, sitting on a chair, chair, legs together, knees together, upright posture, "
           + "A petite fallen angel girl in a full body shot, seated on a chair, the whole chair and her whole body "
             "from the top of her halo to the bottom of the chair fully visible inside the frame with margin around them, "
           + "sitting gracefully on a simple plain wooden chair, facing the viewer, her knees together and her back "
             "straight in an upright elegant posture, her hands resting gently on her lap. "
           + A_CALM + A_BG + A_TAIL)
    neg = A_NEG.replace("furniture, ", "").replace("sitting, ", "") + ", standing, legs spread, crossed legs, ornate chair, throne, sofa, armchair"
    return ("MA20", A_SEED, pos, neg)

def furfur_pose(surf):
    tags, prose, expr, negx = F_POSES[surf]
    pos = F_BASE + PROP_TAGS + tags + F_OUTFIT + FRAME + prose + F_WEAR + PROP_PROSE + F_WINGS + expr + F_BG
    return (f"MF{surf}", F_SEED, pos, F_NEG + negx)

def furfur_pose_expr(surf):
    base, etags, eprose, eneg = F_POSE_EXPR[surf]
    tags, prose, _expr, _nx = F_POSES[base]
    pos = F_BASE + PROP_TAGS + tags + etags + F_OUTFIT + FRAME + prose + F_WEAR + PROP_PROSE + F_WINGS + eprose + F_BG
    return (f"MF{surf}", F_SEED, pos, F_NEG + eneg)

def furfur_sit():
    pos = (F_BASE + PROP_TAGS + "sitting, sitting on a chair, chair, legs dangling, swinging legs, relaxed, happy, "
           + F_EYES + F_OUTFIT
           + "A petite fallen angel girl in a full body shot, seated on a chair, the whole chair and her whole body "
             "from the top of her head to the bottom of the chair fully visible inside the frame with margin around them, "
           + "sitting on a simple plain wooden chair that is a little tall for her, facing the viewer, her short legs "
             "dangling off the front edge of the seat and swinging playfully in the air, her feet not touching the floor, "
             "her hands resting on the seat beside her hips, a relaxed carefree posture. "
           + F_WEAR + PROP_PROSE + F_WINGS
           + "She has a cheerful relaxed expression with a happy open-mouth smile, enjoying herself as she swings her legs. "
           + F_BG)
    neg = (F_NEG_BASE.replace("sitting, ", "").replace("holding book, holding object, ", "")
           + ", pink dress, nightgown, negligee, pajamas" + HAND_NEG
           + ", feet on floor, standing, ornate chair, throne, sofa, armchair" + PROP_NEG)
    return ("MF21", F_SEED, pos, neg)

for s in (6, 7, 8, 9):
    JOBS.append(asta_pose(s))
for s in (46, 47, 48, 49):
    JOBS.append(asta_pose_expr(s))
JOBS.append(asta_sit())
for s in (16, 17, 18, 19):
    JOBS.append(furfur_pose(s))
for s in (56, 57, 58, 59):
    JOBS.append(furfur_pose_expr(s))
JOBS.append(furfur_sit())

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
     "9": {"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":f"maid_pose_{label}_seed{seed}"}}
    }
    data = json.dumps({"prompt": workflow}).encode()
    req = urllib.request.Request("http://127.0.0.1:8188/prompt", data=data, headers={"Content-Type": "application/json"})
    resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
    pid = resp["prompt_id"]
    print("JOB", label, "SEED", seed, "PID", pid, flush=True)
    for i in range(120):
        time.sleep(5)
        h = json.loads(urllib.request.urlopen(f"http://127.0.0.1:8188/history/{pid}", timeout=15).read())
        if pid in h:
            st = h[pid].get("status", {})
            print("JOB", label, "STATUS", st.get("status_str"), flush=True)
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
        print("FAILED", label, r, flush=True)
print("DONE rc=", rc, flush=True)
sys.exit(rc)
