import json, urllib.request, time, sys

# v2.23 生成一括スクリプト。
# 第1部: 夜シェル仮置き差し替え（アスタロト A7 ポーズ6-9/46-49、フルフル N5 ポーズ16-19/56-59、座り20/21）
# 第2部: 通常シェル フルフル全15面の頭身是正（10-15,16-19,56-59,21）
# フルフルには頭身指示（細身・脚長・約6頭身・非ちび）を必ず入れる。基準は現行 surface17 のバランス。
# usage: gen_v223.py [night|master|all]  （既定 all、night を先に実行）

PROP_TAGS = "slender body, long legs, tall proportions, small head, "
PROP_PROSE = ("She has slender, well-balanced proportions with relatively long legs and a smaller head, "
              "about six heads tall, the same height as another girl of similar stature standing beside her, "
              "elegant and natural proportions, not chibi. ")
PROP_NEG = ", chibi, super deformed, sd, short legs, stubby legs, large head, big head, toddler proportions, child proportions, dwarf proportions, short body"

BG = ("Behind her is a completely plain solid bright green background, a single flat uniform green "
      "color filling the entire background, chroma key green screen, no scenery, no floor, no shadows, "
      "no gradient. Clean silhouette, hair, wings and clothes clearly separated from the green background.")
FRAME = ("A petite fallen angel girl in a full body shot, her whole body from the top of her head to the tips "
         "of her feet fully visible inside the frame with margin around her, ")

# ---------- アスタロト A7 (夜) ----------
A_BASE = ("masterpiece, best quality, score_7, fallen angel, 1girl, solo, petite, "
          "deep purple and violet hair, long hair, wavy hair, choppy bangs, golden amber eyes, "
          "round pupils, (pale skin:0.3), gold pendant, halo, ")
A_OUTFIT = ("pale lavender blue silk negligee, light blue-violet silk nightgown, elegant nightgown "
            "with delicate white lace trim, long nightgown falling below the knees, thin shoulder "
            "straps, sheer lavender robe worn open over the nightgown, bare feet, ")
A_TAIL = (" She wears an elegant pale lavender blue silk negligee with delicate white lace trim, tasteful "
          "and modest, the skirt of the nightgown falling below her knees, and over it a sheer lavender "
          "robe worn open, its sleeves and hem flowing softly.")
A_NEG = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
         "cropped, out of frame, cut off, upper body only, close-up, scenery, indoors, outdoors, "
         "furniture, gradient background, multiple girls, sitting, "
         "black and gold dress, off-shoulder dress, long dress, gold trim dress, high heels, shoes, "
         "underwear, bra, panties, lingerie set, excessively revealing, see-through body, "
         "black negligee, black nightgown")
A_CALM = "She has a calm gentle expression, her golden eyes looking softly at the viewer. "
A_FRAME = ("A petite fallen angel girl in a full body shot, her whole body from the top of her halo to the tips "
           "of her feet fully visible inside the frame with margin around her, ")

A_POSES = {
    6: ("standing, own hands together, hands clasped in front, ",
        A_FRAME + "standing straight and facing the viewer, her arms lowered in front of her body with both hands gently clasped together in front of her waist, a calm docile standing posture, not holding anything. ",
        A_CALM, "", 20261101, ""),
    7: ("three-quarter view, own hands together, hands clasped in front of chest, head bowed, worried expression, ",
        A_FRAME + "shown in a three-quarter view with her body turned slightly to the side, both hands clasped together in front of her chest, her head slightly bowed, not holding anything. ",
        "She has a gentle worried expression, her eyebrows slightly raised in concern, gazing quietly toward the viewer. ",
        "", 20262102, ""),
    8: ("holding book, book, old book, ",
        A_FRAME + "standing straight and facing the viewer, hugging a thick old leather-bound book against her chest with both arms. ",
        A_CALM, "holding:", 98101, ""),
    9: ("arms crossed, crossed arms, looking down, confident, ",
        A_FRAME + "standing straight and facing the viewer, her arms firmly crossed over her chest, her chin slightly raised in a confident posture, not holding anything. ",
        "She looks slightly down at the viewer with a composed, mildly condescending, unimpressed expression. ",
        "", 20261101, ""),
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

# ---------- フルフル共通 ----------
F_BASE = ("masterpiece, best quality, score_7, fallen angel, 1girl, solo, petite, "
          "white hair, twintails, hair just past shoulders, curled hair ends, "
          "small pink hair ties, long face-framing sidelocks, choppy bangs, ")
F_EYES = "starry sparkling cyan-blue eyes, star-shaped highlights in eyes, round pupils, "
F_NEG_TAIL = (", halo, purple hair, black hair, dark hair, deer, antlers, horns, tail, animal ears, huge wings, giant wings")
HAND_NEG = ", oversized hands, huge hands, big hands, disproportionate hands, long fingers"
SYMBOL_NEG = ", floating symbols, steam puffs, emphasis lines, motion lines, sparkles"

# 夜 N5
N_SKIN = ("pinkish skin, blush, short black babydoll negligee, black silk nightgown, white lace trim, frills, "
          "nightgown ending above her knees, thin shoulder straps, small white ribbon, bare feet, "
          "white feather wings, two small white feather wings on her back, ")
N_WEAR = ("She wears a cute short black babydoll negligee with white lace trim and frills, tasteful and "
          "modest, its skirt ending above her knees. Two small white feather wings spread slightly behind "
          "her back, modest in size, fully visible inside the frame and not too large. ")
N_NEG = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
         "cropped, out of frame, cut off, upper body only, close-up, scenery, indoors, outdoors, "
         "furniture, gradient background, multiple girls, holding book, holding object, sitting, "
         "gold dress, long dress, underwear, bra, panties, lingerie set, excessively revealing, "
         "pajamas, long pants, trousers, pink negligee, pink nightgown, pink dress" + F_NEG_TAIL)

# 通常 ピンクドレス
M_SKIN = ("pinkish skin, blush, pink sleeveless dress, white frilled shoulder straps, small white bow, "
          "white lace-up criss-cross ribbon on the front of the bodice, gathered waist, "
          "flared skirt with a thin white line near the hem, white frilled petticoat hem under the skirt, "
          "pink mary jane shoes with ankle straps, "
          "white feather wings, two large white feather wings behind her shoulders, ")
M_IDENTITY = ("She is always the same girl with the same face, the same starry sparkling cyan-blue eyes, "
              "the same white twintails with curled ends and pink hair ties, and the same outfit: a pink "
              "sleeveless dress with white frilled shoulder straps, a small white bow and a white lace-up "
              "criss-cross ribbon on the front of the bodice, and a white frilled petticoat hem under the "
              "flared skirt. Two large white feather wings behind her shoulders, fully visible inside the frame. ")
M_NEG = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
         "cropped, out of frame, cut off, upper body only, close-up, scenery, indoors, outdoors, "
         "furniture, gradient background, multiple girls, holding book, holding object, sitting, "
         "black dress, gold dress, long dress" + F_NEG_TAIL)

F_POSES = {
    16: ("leaning forward, bending forward, reaching out, arms reaching toward viewer, open hands, excited, happy, open mouth smile, :d, " + F_EYES,
         "leaning forward toward the viewer with her upper body tilted in eagerly, both arms stretched out toward the viewer with open palms as if reaching out to grab or hug the viewer, an eager pushy posture full of energy. ",
         "She has an eager excited expression, sparkling eyes and a big happy open-mouth smile, thrilled to get closer. ",
         HAND_NEG + ", standing straight, arms hanging at sides, calm expression, frown", 16101),
    17: ("arms spread wide, arms outstretched to the sides, joyful, happy, open mouth smile, :d, " + F_EYES,
         "standing straight and facing the viewer with both arms spread wide open to her sides in delight, her two white feather wings also spread wide behind her shoulders, a joyful welcoming posture. ",
         "She has a bright joyful expression with a big happy open-mouth smile, beaming with delight. ",
         ", arms hanging at sides, folded wings, closed eyes, calm expression, frown", 17102),
    18: ("from behind, back view, three-quarter back view, looking back, looking over shoulder, arms crossed, pout, puffed cheeks, sulky, annoyed, furrowed brows, ",
         "shown from a three-quarter back view with her body turned away from the viewer in a sulk, her arms crossed over her chest, her head turned to look back over her shoulder at the viewer, her white feather wings visible from behind her shoulders. ",
         "She is sulking and pouting, her cheeks puffed, her eyebrows furrowed in annoyance, her mouth in a small displeased pout as she glares back over her shoulder with starry sparkling cyan-blue eyes. ",
         ", body facing viewer, full front view, smile, happy, joyful, open mouth smile", 1031),
    19: ("hands clasped, own hands together, hands clasped in front of chest, begging, pleading, upward gaze, looking up, " + F_EYES,
         "standing straight and facing the viewer, both hands clasped together tightly in front of her chest in a begging gesture, leaning very slightly forward, not holding anything. ",
         "She looks up at the viewer with a pleading upward gaze, her starry eyes sparkling hopefully, her mouth in a small hopeful smile, earnestly begging for a favor. ",
         ", arms hanging at sides, looking down, angry, frown, closed eyes", 1031),
}
F_POSE_EXPR = {
    56: (16, F_EYES + "blush, deep blush, red cheeks, embarrassed, shy, in love, bashful smile, ",
         "She is deeply embarrassed and lovestruck even as she leans in close, her cheeks blushing bright pink, with a small bashful happy smile, her gaze eager but shy. ",
         HAND_NEG + ", standing straight, arms hanging at sides, calm expression, angry, frown, closed eyes"),
    57: (17, "closed eyes, blissful, content, gentle smile, satisfied, ",
         "Her eyes are gently closed in pure bliss, with a satisfied content smile, savoring the happy moment. ",
         ", arms hanging at sides, folded wings, open eyes, looking at viewer, frown"),
    58: (18, "surprised, wide eyes, raised eyebrows, open mouth, :o, ",
         "She looks genuinely surprised as she glances back over her shoulder, her starry sparkling cyan-blue eyes wide open, her eyebrows raised, her mouth open in a small round shape, caught off guard. ",
         SYMBOL_NEG + ", body facing viewer, full front view, closed eyes, calm expression, smile, pout, puffed cheeks"),
    59: (19, F_EYES + "big smile, open mouth smile, :d, very happy, joyful, ",
         "She has a big joyful open-mouth smile, beaming happily up at the viewer as she begs, full of energy and delight, her starry eyes sparkling. ",
         ", arms hanging at sides, looking down, angry, frown, closed eyes, sad, small smile"),
}
# 通常 基本＋表情（10は素、11-15は gen_night_expr の FUR_EXPRS と同じ表情対応）
M_EXPRS = {
    10: (F_EYES + "cheerful smile, gentle smile, happy, ",
         "She has a cheerful gentle smile, her sparkling blue eyes open and looking at the viewer, bright and energetic. ",
         ", frown, angry, closed eyes, sad"),
    11: (F_EYES + "big smile, open mouth smile, :d, very happy, joyful, laughing, ",
         "She has a big joyful open-mouth smile, beaming happily at the viewer, full of energy and delight. ",
         ", frown, angry, closed eyes, sad, calm expression"),
    12: ("blue eyes, sparkling eyes, wide eyes, surprised, raised eyebrows, open mouth, :o, ",
         "She looks genuinely surprised, her eyes wide open, her eyebrows raised, and her mouth open in a small round shape, startled by her own thunder. ",
         ", closed eyes, calm expression, smile"),
    13: (F_EYES + "pout, puffed cheeks, sulky, annoyed, furrowed brows, frown, looking to the side, ",
         "She is sulking and pouting, her cheeks slightly puffed, her eyebrows furrowed in annoyance, her mouth in a small displeased pout, glancing to the side. ",
         ", smile, happy, blush, wide eyes, open mouth"),
    14: (F_EYES + "blush, deep blush, red cheeks, embarrassed, shy, in love, small bashful smile, looking to the side, averted gaze, ",
         "She is deeply embarrassed and lovestruck, her cheeks blushing bright pink, her gaze turned slightly to the side away from the viewer, with a small bashful happy smile. ",
         ", looking at viewer, angry, frown, calm expression"),
    15: ("closed eyes, serene expression, gentle smile, sleepy, content, ",
         "Her eyes are gently closed, with a calm serene and content expression and a soft peaceful smile, as if satisfied and a little sleepy. ",
         ", open eyes, looking at viewer, frown, angry"),
}

JOBS = []  # (group, label, seed, positive, negative)

def asta_pose(surf):
    tags, prose, expr, _h, seed, _x = A_POSES[surf]
    neg = A_NEG if surf != 8 else A_NEG.replace("holding book, ", "").replace(", holding object", "")
    if surf == 8:
        neg = A_NEG  # A_NEG に holding book は含まれない
    pos = A_BASE + A_OUTFIT + tags + prose + expr + BG.replace("hair, wings and clothes", "hair and nightgown") + A_TAIL
    return ("night", f"NA{surf}", seed, pos, neg)

def asta_pose_expr(surf):
    base, etags, eprose, eneg = A_POSE_EXPR[surf]
    tags, prose, _expr, _h, seed, _x = A_POSES[base]
    pos = A_BASE + A_OUTFIT + tags + etags + prose + eprose + BG.replace("hair, wings and clothes", "hair and nightgown") + A_TAIL
    return ("night", f"NA{surf}", seed, pos, A_NEG + eneg)

def furfur_pose(group, surf, skin, wear_or_identity, negbase):
    tags, prose, expr, negx, seed = F_POSES[surf]
    if group == "night":
        pos = F_BASE + PROP_TAGS + tags + skin + FRAME + prose + wear_or_identity + PROP_PROSE + expr + BG
    else:
        pos = F_BASE + PROP_TAGS + tags + skin + FRAME + prose + wear_or_identity + PROP_PROSE + expr + BG
    return (group, f"{'NF' if group=='night' else 'MF'}{surf}", seed, pos, negbase + negx + PROP_NEG)

def furfur_pose_expr(group, surf, skin, wear_or_identity, negbase):
    base, etags, eprose, eneg = F_POSE_EXPR[surf]
    tags, prose, _expr, _nx, seed = F_POSES[base]
    # 表情違いではポーズタグから表情タグを除き、表情タグに置換する（元スクリプトの流儀）
    pos = F_BASE + PROP_TAGS + tags + etags + skin + FRAME + prose + wear_or_identity + PROP_PROSE + eprose + BG
    return (group, f"{'NF' if group=='night' else 'MF'}{surf}", seed, pos, negbase + eneg + PROP_NEG)

def furfur_sit(group, skin, wear_or_identity, negbase):
    pos = (F_BASE + PROP_TAGS + "sitting, sitting on a chair, chair, legs dangling, swinging legs, relaxed, happy, "
           + F_EYES + skin
           + "A petite fallen angel girl in a full body shot, seated on a chair, the whole chair and her whole body "
             "from the top of her head to the bottom of the chair fully visible inside the frame with margin around them, "
           + "sitting on a simple plain wooden chair that is a little tall for her, facing the viewer, her short legs "
             "dangling off the front edge of the seat and swinging playfully in the air, her feet not touching the floor, "
             "her hands resting on the seat beside her hips, a relaxed carefree posture. "
           + wear_or_identity + PROP_PROSE
           + "She has a cheerful relaxed expression with a happy open-mouth smile, enjoying herself as she swings her legs. "
           + BG)
    neg = negbase.replace("sitting, ", "").replace("holding book, holding object, ", "") + HAND_NEG + ", feet on floor, standing, ornate chair, throne, sofa, armchair" + PROP_NEG
    return (group, f"{'NF' if group=='night' else 'MF'}21", 21101, pos, neg)

def asta_sit():
    pos = (A_BASE + A_OUTFIT
           + "sitting, sitting on a chair, chair, legs together, knees together, upright posture, "
           + "A petite fallen angel girl in a full body shot, seated on a chair, the whole chair and her whole body "
             "from the top of her halo to the bottom of the chair fully visible inside the frame with margin around them, "
           + "sitting gracefully on a simple plain wooden chair, facing the viewer, her knees together and her back "
             "straight in an upright elegant posture, her hands resting gently on her lap. "
           + A_CALM + BG.replace("hair, wings and clothes", "hair, nightgown and chair") + A_TAIL)
    neg = A_NEG.replace("furniture, ", "").replace("sitting, ", "") + ", standing, legs spread, crossed legs, ornate chair, throne, sofa, armchair"
    return ("night", "NA20", 201103, pos, neg)

def furfur_master_base(surf):
    etags, eprose, eneg = M_EXPRS[surf]
    pos = (F_BASE + PROP_TAGS + etags + M_SKIN + FRAME
           + "standing straight and facing the viewer, arms relaxed and hanging naturally at her sides, not holding anything, hands empty. "
           + M_IDENTITY + PROP_PROSE + eprose + BG)
    return ("master", f"MF{surf}", 1031, pos, M_NEG + eneg + PROP_NEG)


M_SKIN = M_SKIN.replace("white feather wings, two large white feather wings behind her shoulders, ",
                        "white feather wings, two small white feather wings behind her shoulders, ")
M_IDENTITY = M_IDENTITY.replace("Two large white feather wings behind her shoulders, fully visible inside the frame. ",
                                "Two small white feather wings behind her shoulders, compact in size, fully visible inside the frame. ")
WING_NEG = ", huge wings, giant wings, large wings, long wings, wings reaching the floor, oversized wings"
for s in (10, 11, 12, 13, 14, 15):
    g, label, seed, pos, neg = furfur_master_base(s)
    if s == 14:
        neg = neg + ", closed eyes"
    JOBS.append((g, label, seed, pos, neg + WING_NEG))
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
     "9": {"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":f"v223_{label}_seed{seed}"}}
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

which = "master"
rc = 0
for group, label, seed, pos, neg in JOBS:
    r = run(label, seed, pos, neg)
    if r != 0:
        rc = r
        print("FAILED", label, r, flush=True)
print("DONE rc=", rc, flush=True)
sys.exit(rc)
