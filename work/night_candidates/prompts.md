# 夜セット（第2シェル）候補 生成記録

生成日: 2026-11-05
生成スクリプト: `work/gen_night_candidates.py`（WSL 実行、CottonAnima base1）
共通条件: 832×1216、30step、CFG 4.0、er_sde、scheduler simple、緑一色背景・全身立ち姿・腕は体の横・手は空（既存の立ち絵ブループリント踏襲）
選択用プレビュー: `preview_all.png`（統合）／`preview_group_A.png`／`preview_group_P.png`／`preview_group_N.png`（生成: `work/make_night_preview.py`）

## A群：アスタロト ネグリジェ（ファイル名 A{n}_seed{seed}.png）

positive（A1〜A3共通）:
```
masterpiece, best quality, score_7, fallen angel, 1girl, solo, petite, deep purple and violet hair, long hair, wavy hair, choppy bangs, golden amber eyes, round pupils, (pale skin:0.3), gold pendant, halo, black silk negligee, deep purple silk nightgown, elegant nightgown with delicate lace trim, knee-length nightgown, thin shoulder straps, bare feet, calm gentle smile, sleepy serene expression, A petite fallen angel girl standing straight and facing the viewer in a full body shot, her whole body from the top of her halo to the tips of her feet fully visible inside the frame with margin around her, arms relaxed and hanging naturally at her sides, not holding anything, hands empty. Behind her is a completely plain solid bright green background, a single flat uniform green color filling the entire background, chroma key green screen, no scenery, no floor, no shadows, no gradient. Clean silhouette, hair and nightgown clearly separated from the green background. She wears an elegant black and deep purple silk negligee with delicate lace trim along the neckline and hem, tasteful and modest, the skirt of the nightgown falling to around her knees.
```
A4 は上記に `sheer black lace robe worn open over the nightgown` を足し、末尾の文章を「…and over it a sheer black lace gown robe worn open, its long sleeves and hem flowing softly.」に差し替えたもの。

negative（A群共通）:
```
worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, cropped, out of frame, cut off, upper body only, close-up, scenery, indoors, outdoors, furniture, gradient background, multiple girls, holding book, holding object, sitting, black and gold dress, off-shoulder dress, long dress, gold trim dress, high heels, shoes, underwear, bra, panties, lingerie set, excessively revealing, see-through body
```

| 番号 | seed | 備考 |
|---|---|---|
| A1 | 20261111 | 膝丈の深紫ネグリジェ、レース裾。眠そうな半眼が夜らしい |
| A2 | 111101 | A1と同系統でやや丈短め、ペンダント大きめ |
| A3 | 777101 | 膝上の短め丈。笑顔寄り |
| A4 | 424201 | 薄手の黒レースガウン羽織り案。ガウン裾が床まで引きずる形で、キーイング時に裾処理の検討が必要 |

## P群：フルフル パジャマ（ファイル名 P{n}_seed{seed}.png）

positive（P群共通）:
```
masterpiece, best quality, score_7, fallen angel, 1girl, solo, petite, white hair, twintails, hair just past shoulders, curled hair ends, blue eyes, sparkling eyes, round pupils, pinkish skin, blush, cheerful smile, gentle smile, happy, white feather wings, two small white feather wings on her back, pink pajamas, frilled pajama set, long-sleeved pajama top with white frills and a small ribbon, long pajama pants, fluffy pink slippers, A petite fallen angel girl standing straight and facing the viewer in a full body shot, her whole body from the top of her head to the tips of her feet fully visible inside the frame with margin around her, arms relaxed and hanging naturally at her sides, not holding anything, hands empty. She wears a cute pink pajama set, a long-sleeved buttoned pajama top with white frills and a small ribbon at the chest, and matching long pajama pants. Two small white feather wings spread slightly behind her back, modest in size, fully visible inside the frame and not too large. She has a cheerful gentle smile, her sparkling blue eyes open and looking at the viewer, bright and energetic. Behind her is a completely plain solid bright green background, a single flat uniform green color filling the entire background, chroma key green screen, no scenery, no floor, no shadows, no gradient. Clean silhouette, hair, wings and clothes clearly separated from the green background.
```
negative（P群）: 下記フルフル共通 negative に `dress, skirt, nightgown, negligee` を追加。

| 番号 | seed | 備考 |
|---|---|---|
| P1 | 20261112 | 髪が低めの緩いツインテール寄り（他2点よりツインテール感が弱い）。衣装・目・翼は仕様通り |
| P2 | 111201 | 高めツインテール＋カール毛先、開いた笑顔。頭周りにキラキラ浮遊物あり（キーイングで除去可） |
| P3 | 777201 | ツインテール＋歯見せ笑顔。足元に濃い影ブロックあり（キーイング時注意） |

## N群：フルフル 短いネグリジェ（ファイル名 N{n}_seed{seed}.png）

positive（N群共通）:
```
masterpiece, best quality, score_7, fallen angel, 1girl, solo, petite, white hair, twintails, hair just past shoulders, curled hair ends, blue eyes, sparkling eyes, round pupils, pinkish skin, blush, cheerful smile, gentle smile, happy, white feather wings, two small white feather wings on her back, short pink babydoll negligee, white and pink silk nightgown, lace trim, frills, nightgown ending above her knees, thin shoulder straps, small ribbon, bare feet, A petite fallen angel girl standing straight and facing the viewer in a full body shot, her whole body from the top of her head to the tips of her feet fully visible inside the frame with margin around her, arms relaxed and hanging naturally at her sides, not holding anything, hands empty. She wears a cute short pink babydoll negligee with white lace trim and frills, tasteful and modest, its skirt ending above her knees. Two small white feather wings spread slightly behind her back, modest in size, fully visible inside the frame and not too large. She has a cheerful gentle smile, her sparkling blue eyes open and looking at the viewer, bright and energ
...[truncated 911 chars]