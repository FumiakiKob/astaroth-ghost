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
---

# 第2便（2026-11-05追加生成）：色替え候補

生成スクリプト: `work/gen_night_candidates2.py`（WSL 実行、条件は第1便と同一）
選択用プレビュー: `preview_round2.png`（第2便のみの統合コラージュ、番号ラベル付き）
背景: ユーザーの評「どれも可愛いが通常版と似すぎている。特にフルフルのネグリジェは普段着とよく似ている。他の色も見せて」を受け、色で明確に差をつけることが目的。

## A群（第2便）：アスタロト ネグリジェ別色（ファイル名 A{n}_seed{seed}.png）

共通部は第1便 A 群と同一（ASTA_BASE＋立ち姿プロース）。衣装部のみ各色に差し替え。
negative は第1便 A 群に `black negligee, black nightgown` を追加したもの。A5／A6／A8 はさらに `deep purple nightgown, purple nightgown` を追加（A7 はラベンダー系のため追加なし）。

- A5 positive 衣装部: `white silk negligee, ivory white silk nightgown, elegant nightgown with delicate white lace trim, knee-length nightgown, thin shoulder straps` ＋末尾文「She wears an elegant ivory white silk negligee with delicate white lace trim along the neckline and hem, tasteful and modest, the skirt of the nightgown falling to around her knees.」
- A6 positive 衣装部: `wine red silk negligee, deep red silk nightgown, elegant nightgown with delicate black lace trim, short nightgown ending above the knees, thin shoulder straps` ＋末尾文「She wears an elegant wine red silk negligee with delicate black lace trim along the neckline and hem, tasteful and modest, the skirt of the nightgown ending above her knees.」
- A7 positive 衣装部: `pale lavender blue silk negligee, light blue-violet silk nightgown, elegant nightgown with delicate white lace trim, long nightgown falling below the knees, thin shoulder straps, sheer lavender robe worn open over the nightgown` ＋末尾文「She wears an elegant pale lavender blue silk negligee with delicate white lace trim, tasteful and modest, the skirt of the nightgown falling below her knees, and over it a sheer lavender robe worn open, its sleeves and hem flowing softly.」
- A8 positive 衣装部: `emerald green silk negligee, deep green silk nightgown, elegant nightgown with delicate gold lace trim, knee-length nightgown, thin shoulder straps` ＋末尾文「She wears an elegant emerald green silk negligee with delicate lace trim along the neckline and hem, tasteful and modest, the skirt of the nightgown falling to around her knees.」

| 番号 | seed | 備考 |
|---|---|---|
| A5 | 20261211 | アイボリー白、膝丈、白レース縁。普段着（黒×金）と最も対照的 |
| A6 | 121201 | ワインレッド、膝上の短め丈、黒レース縁 |
| A7 | 777401 | 淡いラベンダーブルー、ロング丈＋シアーなラベンダーのガウン羽織り。A4と同様ガウン裾が床に広がる形で、キーイング時に裾処理の検討が必要 |
| A8 | 424501 | エメラルドグリーン、膝丈 |

## P群（第2便）：フルフル パジャマ別色（ファイル名 P{n}_seed{seed}.png）

共通部は第1便 P 群と同一（FUR_BASE＋立ち姿プロース）。衣装部のみ差し替え。
negative は第1便 P 群に `pink pajamas` を追加したもの。

- P4 positive 衣装部: `light blue pajamas, star and crescent moon pattern pajamas, long-sleeved pajama top with white frills and a small ribbon, long pajama pants, fluffy light blue slippers` ＋着用文「She wears a cute light blue pajama set printed with small white stars and crescent moons, a long-sleeved buttoned pajama top with white frills and a small ribbon at the chest, and matching long pajama pants.」
- P5 positive 衣装部: `mint green pajamas, star pattern pajamas, long-sleeved pajama top with white frills and a small ribbon, long pajama pants, fluffy mint green slippers` ＋着用文「She wears a cute mint green pajama set printed with small white stars, a long-sleeved buttoned pajama top with white frills and a small ribbon at the chest, and matching long pajama pants.」
- P6 positive 衣装部: `lavender pajamas, crescent moon pattern pajamas, long-sleeved pajama top with white frills and a small ribbon, long pajama pants, fluffy lavender slippers` ＋着用文「She wears a cute lavender pajama set printed with small white crescent moons, a long-sleeved buttoned pajama top with white frills and a small ribbon at the chest, and matching long pajama pants.」

| 番号 | seed | 備考 |
|---|---|---|
| P4 | 20261212 | 水色、星と三日月柄。低めツインテール。髪の一部に透かし状の微かな文字様の乱れあり（拡大時のみ視認できる程度） |
| P5 | 121501 | ミントグリーン、星柄。ツインテールが短く、他2点よりツインテール感が弱い |
| P6 | 777501 | ラベンダー、三日月柄。低めツインテール。頭周りにキラキラ浮遊物あり（キーイングで除去可） |

## N群（第2便）：フルフル 短いネグリジェ別色（ファイル名 N{n}_seed{seed}.png）

共通部は第1便 N 群と同一（FUR_BASE＋立ち姿プロース）。衣装部のみ差し替え。
negative は第1便 N 群に `pink dress` を追加したもの。N5 は黒ドレス系を許可するため共通 negative から `black dress` を除き、`pink negligee, pink nightgown` を追加。N6 は `pink negligee, pink nightgown` を追加。

- N4 positive 衣装部: `short white babydoll negligee, white silk nightgown, white lace trim, frills, nightgown ending above her knees, thin shoulder straps, small pink ribbon, pink ribbon accents, bare feet` ＋着用文「She wears a cute short white babydoll negligee with white lace trim and frills and small pink ribbon accents, tasteful and modest, its skirt ending above her knees.」
- N5 positive 衣装部: `short black babydoll negligee, black silk nightgown, white lace trim, frills, nightgown ending above her knees, thin shoulder straps, small white ribbon, bare feet` ＋着用文「She wears a cute short black babydoll negligee with white lace trim and frills, tasteful and modest, its skirt ending above her knees.」
- N6 positive 衣装部: `short light blue babydoll negligee, light blue silk nightgown, white lace trim, frills, nightgown ending above her knees, thin shoulder straps, small white ribbon, bare feet` ＋着用文「She wears a cute short light blue babydoll negligee with white lace trim and frills, tasteful and modest, its skirt ending above her knees.」

| 番号 | seed | 備考 |
|---|---|---|
| N4 | 20261213 | 白、白レース＋ピンクのリボンで彼女らしさを残した。ツインテール明確 |
| N5 | 121601 | 黒、白レース縁。白髪・白翼とのモノクロ対比が強く、普段着と最も別物に見える |
| N6 | 777601 | 水色、白レース縁。ツインテール明確 |
