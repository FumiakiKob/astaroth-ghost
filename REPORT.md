# アスタロト用 SSP ゴースト v1 制作レポート

制作日: 2026-11-01
成果物: `astaroth.nar`（1,868,196 bytes / zip 30エントリ）、`surface0.png`（最終トリミング済み透明PNG）、`src_images/`（生成元絵3枚）

## 1. シェル用立ち絵の生成

- 経路: `~/workspace/scripts/muse-ssh` → WSL「Muse」(100.127.63.24) → ComfyUI API (127.0.0.1:8188)。接続・応答とも正常。
- ワークフロー（日次イラスト生成 `gen_daily_20261031.py` を雛形に改変）:
  - UNETLoader: cottonanima_base1.safetensors / CLIPLoader: qwen_3_06b_base.safetensors (type=stable_diffusion) / VAELoader: qwen_image_vae.safetensors
  - KSampler: 30 steps / CFG 4.0 / er_sde / simple、latent 832×1216
- プロンプト（positive）:
  - タグ: `masterpiece, best quality, score_7, fallen angel, 1girl, solo, petite, deep purple and violet hair, long hair, wavy hair, choppy bangs, golden amber eyes, round pupils, (pale skin:0.3), gold pendant, halo, black and gold off-shoulder dress, elegant long dress with gold trim, gold chain necklace with demon crest pendant, black heeled shoes`
  - 文章指定: 全身が余白付きで収まる正面の直立ポーズ、腕は体の横に自然に下ろし手は空、背景は全面均一な明るい緑一色（クロマキー用、風景・床・影・グラデーションなし）
  - negative に cropped / out of frame / scenery / gradient background / holding book 等を指定
- 生成3シードと選定:
  - **seed 20261101 = 採用**。直立対称ポーズ、両足の靴まで完全収納、背景が純粋な緑（RGB≈53,253,40）でキーイング最適
  - seed 1101 = 次点。全身は収まっているが一歩踏み出した歩行ポーズで、足下に大きな影と光輪の映り込みあり
  - seed 777001 = 不採用。ドレスの裾が床に広がり画面下端に接触、スリット入りでシェル向きでない

## 2. 背景除去（透明PNG化）

- 処理はWSL内（ComfyUI venv の Python: PIL 13.0 / numpy 2.5 / scipy 1.18）で実施。rembg は未導入だったため、単色背景を活かした自前キーイングを採用:
  1. 「緑優位（G − max(R,B) ≥ 18）」画素を通って画像端からフラッドフィルし、到達領域を背景として除去（地面の影もこの経路で除去）
  2. 緑優位度の減衰関数を乗算し、光輪の内側に囲まれた背景領域と縁の緑フリンジを除去
  3. 可視フリンジにデスピル（G を max(R,B)+10 に制限）、アルファに軽いガウシアン平滑化
- 検証結果（数値）:
  - アルファ>128 の外接矩形 x:192..653 / y:7..1212、四隅のアルファは全て0
  - 光輪はリングとして保持（上端70行の不透明画素 1,930px、リング内側中心のアルファ=0 を確認）
  - 地面の影は除去済み（足下拡大で確認）。濃紺・白の両背景に合成して縁を確認し、大きな破綻なし
  - 最終トリミング: (184,0)-(662,1216) → **478×1216**
- 軽微な残存物（v1では許容、差分追加時に要再確認）: 両靴の間に小さな青緑色の点、スカート左縁に沿った細い線（元絵由来の描線）

## 3. ゴースト本体（YAYA最小構成）

- 土台: 公式テンプレート「紺野ややめ」（GitHub: YAYA-shiori/konnoyayame、2026-11-01 clone、システム辞書 yaya-dic サブモジュール c2e788f 含む）
- `ghost/master/descript.txt`: name=アスタロト、sakura.name=アスタロト、shiori=yaya.dll、sstp.allowunspecifiedsend=1。相方（kero）は定義せず一人構成
- 辞書は最小化: `dic/normal/` には自作2ファイルのみ
  - `astaroth_bootend.dic`: OnFirstBoot / OnBoot / OnClose の短い応答のみ
  - `astaroth_string.dic`: On_username のみ
  - テンプレートのランダムトーク、メニュー、コミュニケート、マウス反応、時報などは全て削除（未定義イベントには応答しない）
  - 緊急時辞書（dic/emerg）とシステム辞書（dic/system）はテンプレートのまま同梱
- `shell/master/`: descript.txt、surfaces.txt（surface0 に Head/Face/Bust の当たり判定。当たり判定座標はトリミング後画像 478×1216 基準で目視推定）、surface0.png（478×1216）、surface10.png（100×100 完全透明ダミー）
- `install.txt`: type=ghost、directory=astaroth
- サーフェス番号の予約（nar内 readme.txt と surfaces.txt のコメントに明記）:
  - 0=通常（実装済み）/ 1=笑顔 / 2=驚き / 3=呆れ・不機嫌 / 4=照れ / 5=目閉じ / 6以降=ポーズ差分

## 4. SSTP到達性の確認（スクリプト送信なし）

- WSL内から Windows ホスト側IP:9801 への TCP接続のみ試行（データは一切送っていない。猫刻への刺激なし）
- 宛先の手掛かり: デフォルトゲートウェイ **172.26.240.1**（`ip route` の default via）。resolv.conf の nameserver は Tailscale DNS (100.100.100.100) でホストIPの手掛かりにはならなかった
- **結果: タイムアウト（到達不可）**。SSPのSSTPは現状 Windows の localhost で待ち受けているとみられ、WSL(NAT) 側からは届かない。ファイアウォールで遮断されている可能性も含む
- 対処候補（いずれもユーザーの判断・手作業が必要なため未実施）:
  1. SSP側に外部からのSSTP受け付け設定があれば有効化＋Windowsファイアウォール許可
  2. Windows側に 9801 のリレー（portproxy 等）を置いて 127.0.0.1:9801 へ転送
  3. WSLのネットワークを mirrored モードへ変更（既存のTailscale/SSH構成への影響が大きいので慎重に）
- 注意: ゲートウェイIP (172.26.240.x) はWSL再起動で変わり得るため、送信側スクリプトでは都度 `ip route` から取得すること

## 5. 音声パイプライン（残課題）

- 再生音声の形式はWAVにこだわらずMP3でよい（2026-11-01決定）。**irodoriのWAV出力をffmpeg等でMP3に変換して \_v で再生する想定**
- パイプライン全体（未構築）: チャット側 → WSLで irodori 合成（美汐参照セット）→ MP3変換 → WSL内の共有/受け渡し経路でSSPが読める場所へ配置 → SSTPで `IfGhost: アスタロト` + `\_v[音声ファイル]` 入りスクリプトを送信
- 上記4の到達性が解けないと送信フェーズに進めない

## 6. ユーザーの手作業（導入手順）

1. SSPを起動する（猫刻が固まっている場合はSSP自体を再起動してから）
2. `astaroth.nar` を起動中のゴーストへドラッグ＆ドロップしてインストールする
3. SSPのメニュー/エクスプローラからゴースト「アスタロト」を呼び出す（猫刻と同時起動できる想定）
4. 確認ポイント:
   - 立ち絵（黒と金のドレス）が表示されるか
   - 起動トーク「来たわね、貴方。……」がバルーンに出るか
   - バルーンに「致命的エラー発生」と出る場合は辞書エラー（緊急時辞書に落ちている）ので、その旨を報告してほしい
   - 終了時に固まらないか

## 追記（2026-11-01 実機確認と v1.1 修正）

- ユーザーが導入：立ち絵表示 OK、起動トーク OK、**背景透過 NG**。
- 原因：SSPのサーフェス透過は既定では「左上ドットの色＝透過色」の色抜き方式。PNGのアルファチャンネルを使うにはシェルdescript.txtへの `seriko.use_self_alpha,1` 記述が必要で、v1には無かった（UKADOC「シェルの作成」参照）。背景画素のRGBが単一色でなかったため色抜きも効かず、緑背景がほぼそのまま残った。
- v1.1 修正（同日）：
  1. `shell/master/descript.txt` に `seriko.use_self_alpha,1` を追加
  2. `surface0.pna` / `surface10.pna`（アルファをグレースケール化したもの）を併置し二重化
  3. surface0.png の完全透明画素のRGBを (0,255,0) に統一（左上＝透過色の色抜き経路でも全面が抜けるように。不透明画素との色衝突は0件を数値確認）
  4. nar再ビルド：32エントリ / 1,724,592 bytes。pnaとアルファの一致、descript内容を検証済み
- 再導入して透過が直ったかの確認待ち。

## 7. 未検証事項

- SSP実機での表示・起動・終了は未検証（インストールはユーザーの手作業として残したため）
- 未定義イベント（メニュー操作、話しかける、なでる等）に対するYAYAの応答挙動は実機未確認。v1では無反応想定だが、実機でエラー表示が出る場合はスタブ追加が必要
- ファイル名 `surface0.png`（テンプレートは `surface0000.png` 形式）でSSPがサーフェス0として認識する想定だが未検証。認識されなければリネームで対処可能
- バルーン位置（offset 0,0 で仮置き）、当たり判定座標は実機での見た目に合わせて要調整の可能性あり
- まばたきアニメーション、表情差分、アイコンは v1 未実装（将来追加）

## 追記2（2026-11-01 音声パイプライン完成）

長い切り分けの末、以下の構成で実音を確認し完成とした：
- SSTP **SEND** で送ったスクリプトでは音声は一切鳴らない（ファイルの場所・形式・パス表記によらない）。`\_v` は引数がバルーンに文字表示され、`\![sound,play]` は実行されても無音だった。HTTP URLはSSPが取得に来ない。
- SSTP **NOTIFY**（Event: OnAstarothSay、Reference0=音声パス、Reference1=文面）で辞書がスクリプトを返し `\![sound,play]` で鳴らす経路なら鳴る。ゴースト内相対パス・UNC（/tmp配置）の両方で確認。
- ただしUNCは配置場所依存：`/home/muse` 配下（750）はSSPから読めず無音、`/tmp` は可。エクスプローラーからはホーム配下も開けるため、SSP側のアクセス主体の違いとみられる。
- 実運用：WSL `~/voice_work/say.py "文面"` → irodori合成（美汐参照8クリップ、約25秒）→ `~/voice_work/out/` に保存し `/tmp/astaroth_voice/` へコピー → Reference0=`\\wsl.localhost\Muse\tmp\astaroth_voice\<file>` でNOTIFY（宛先はゲートウェイIP:19801中継、自動取得）。
- 辞書 `dic/normal/astaroth_voice.dic` の OnAstarothSay が受け口。テスト用同梱 voice_test.wav は残置（無害）。

## 追記3（2026-11-01 表情差分 surface1〜5 制作 ※nar未ビルド）

- 生成：v1ワークフロー踏襲（`work/gen_expr.py`、WSL ComfyUI、832×1216、30step/CFG4/er_sde）。表情ごとに3シード（20261101 / 91x01 / 91x02）生成し選定。**全表情とも seed 20261101 を採用**（surface0と同シードで構図・ドレス・装飾が最も一致。次点：surface1の91101は穏やかな笑みだが腕の開きが大きい、など）。
  - 1=笑顔（明るい笑み）/ 2=驚き（見開いた目＋小さく開いた口）/ 3=呆れ・不機嫌（半眼の睨み＋しかめ面）/ 4=照れ（頬の赤み＋俯き気味に逸らした視線）/ 5=目閉じ（穏やかな閉眼＋微笑み）
- キーイング：`work/finalize_expr.py`（keying2と同一処理＋浮遊アーティファクト除去）。全画像に漫画記号（溜息の息・汗マーク等）が背景に浮いていたため、連結成分で「本体・2000px以上・幅110px以上の成分（光輪）」以外を除去（surface3の息マーク1565px等を除去済み）。
- 正規化：全て 478×1216（本体中心でセンタリング、全面高さ維持）、透明画素RGB=(0,255,0)統一、.pna併置（PNGのアルファと完全一致を検証）。実測bboxは全表情で x:4〜14..464〜474 / y:9〜21..1211〜1212 と surface0 にほぼ一致。
- 配置：`build/astaroth/shell/master/surface1〜5.png/.pna`。surfaces.txt に surface1〜5 を追加し、当たり判定は surface0 と同一座標を流用（顔位置が揃っているため）。
- プレビュー：`work/expressions_preview/`（個別の暗背景合成・上半身、surface0と並べた比較シート2種）。選定用シートは `work/sheets_tmp/`、採用元絵は `src_images/astaroth_exprN_seed20261101.png`。
- 注意点：surface3・4 の光輪は元絵由来でやや金色寄り（surface0は白色）。実害は小さいと判断し許容。辞書（.dic）は未変更で、表情を実際に使うにはトーク側で \s[1]〜\s[5] の指定が必要（時報統合ビルド時に辞書と一緒に実装する想定）。

## 追記4（2026-11-03 SSTP NOTIFY からネットワーク更新を起動するフック追加 / nar v2.5）

- 背景：外部から SSTP SEND で直接送ったスクリプトの `\![updatebymyself]`（および `update,ghost`、強制指定 `ghost+shell+balloon`）は、SSP が 200 OK で受理するだけで実行せず、配信サーバへのアクセスも一切発生しないことを実機で確認。対して SSTP NOTIFY で SHIORI イベントを起こし、辞書が返したスクリプトはゴースト自身の発話として実行される（OnFurfurTalkTest / OnAstarothHourlyTest / OnAstarothSay で実証済みの経路）。この方式で更新タグを辞書側から実行させる。
- 実装：`dic/normal/astaroth_update.dic`（更新報告トーク用辞書）にフックイベント **OnAstarothUpdateRequest** を追記（ファイル追加なし、_loading_order.txt は変更なし・正書式のまま）。返却スクリプトは `'\0\s[0]更新を確認するわ、貴方。\![updatebymyself]\e'`。開始の一言だけを喋って更新タグを実行し、結果報告は既存の OnUpdateComplete / OnUpdateFailure に任せる構成（OnUpdateBegin で喋らない方針と競合せず、二重バルーンにならない）。
- 配信反映：ビルドツリーと WSL 配信フォルダ `~/ghost_update/astaroth/` の両方を更新し MD5 一致を確認（astaroth_update.dic：新 b405e41309fe25612d38859a6d722c1a、旧 ca50fe73b419f5b10d4c668707b558de）。`gen_update_file.py` で updates2.dau を再生成（81レコード、8,413 bytes）し、全レコードの MD5 再計算で不一致0・未収録ファイル0を検証。今回の配信差分は astaroth_update.dic の1件のみ。
- nar：v2.5 として再ビルド（`zip -D` でディレクトリエントリなし、v2.4 とエントリ一覧81件が完全一致）。`astaroth.nar` 差し替え＋ `astaroth_v2.5_backup.nar` 保存、いずれも 9,629,184 bytes。zip 読み戻しで astaroth_update.dic の MD5 一致とフック収録、_loading_order.txt の書式違反0件を確認。
- 実機テスト手順（未実施）：(1) ユーザーが手動で一度「ネットワーク更新」を実行し、このフック入り辞書を取り込む。(2) 以後、アスタロト側が SSTP NOTIFY（Event: OnAstarothUpdateRequest）を送ると、ゴーストが一言喋って `\![updatebymyself]` を実行するはず。(3) 成否は配信サーバ（ghost-update-server）のアクセスログに updates2.dau / 差分ファイルの GET が記録されることと、完了後の報告トーク（更新あり／なし／失敗）で確認する。

## 追記5（2026-11-03 フルフルの時報一言に音声付与 / nar v2.6）

- 背景：時報 v2 でテキストのみだったフルフルの一言8本（0・6・8・11・12・15・18・23時）に、完成したフルフルの声（Irodori-TTS v4.1-Small＋Speaker Inversion 最終埋め込み `akane_v2/checkpoint_final.speaker.safetensors`）で音声を付けた。
- 合成：WSL `~/voice_work/furfur_hourly/` で8本を合成（チェックポイントは v4.1-Small ローカルスナップショット 2b28324d…、シードは従来テストと同条件で未指定）。WAV→ffmpeg で既存時報音声と同一形式（48kHz/mono/128kbps MP3）に変換。長さは 1.82〜3.12 秒、mean volume −17.2〜−19.4 dB で無音・異常なしを確認。配置は `ghost/master/voice/furfur_hour_XX.mp3`。
- 読み調整（合成入力のみ、表示テキストは原稿の漢字表記のまま不変）：11時「お腹→おなか／時計→とけい／鳴→な」、15時「私→わたし」、18時「恋→こい」。他5本は調整なし。
- 辞書改修：`astaroth_hourly.dic` を v3 とし、該当8時刻でフルフルのスコープ（`\1\s[NN]`）開始位置に `\![sound,play,voice/furfur_hour_XX.mp3]` を追加（アスタロト側の既存方式に倣う）。`_loading_order.txt` は変更なし・正書式のまま。
- 配信反映：ビルドツリーと WSL 配信フォルダ `~/ghost_update/astaroth/` の両方へ辞書＋MP3 8本をコピーし、辞書の MD5 一致を確認（astaroth_hourly.dic：36c4917b86555dcf30efe5a10bc1f5fc）。`gen_update_file.py` で updates2.dau を再生成（89レコード、9,285 bytes）し、全レコードの MD5 再計算で不一致0・未収録ファイル0を検証。今回の配信差分は astaroth_hourly.dic＋furfur_hour_*.mp3 8本の計9件。
- nar：v2.6 として再ビルド（`zip -D`、89エントリ＝v2.5 の81＋新規MP3 8）。`astaroth.nar` 差し替え＋ `astaroth_v2.6_backup.nar` 保存、いずれも 9,951,744 bytes。zip 読み戻しで追加エントリが新規MP3 8本のみ・削除0、辞書とMP3 8本の MD5 一致、`dic/normal/_loading_order.txt` の書式違反0件を確認（system 辞書側の dicif/dicdir 行はテンプレート由来の正規書式で変更なし）。
- 実機確認手順（未実施）：(1) アスタロト側が SSTP NOTIFY（Event: OnAstarothUpdateRequest）でネットワーク更新を起動し、差分9件を取り込む。(2) 時報テストフック OnAstarothHourlyTest（Reference0=時）で対象時刻（例：12）を指定し、アスタロトの時報音声に続いてフルフルの一言が「ごはん、ごはん！」と声付きで鳴ることを確認する。

## 追記6（2026-11-03 他ゴースト言及＋インストール時トークの辞書実装 / nar v2.7）

承認済み原稿2本（TALKS_OTHER_GHOST.md / TALKS_INSTALL.md）を新規辞書2本に実装した。どちらも音声なし（テキストのみ）。

- **`dic/normal/astaroth_otherghost.dic`**（他ゴースト言及、全24本＝A汎用12＋B個別12）:
  - 検知は原稿メモ通り：来た=OnOtherGhostBooted（Ref2/Ref0）、替わった=OnOtherGhostChanged（**新相手は Ref5/Ref1**、Ref0 は前任のため不使用）、帰った=OnOtherGhostClosed（Ref2/Ref0）、消えた=OnOtherGhostVanished（無言でフラグ掃除のみ）、呼ばれた=OnGhostCalled（Ref2/Ref0、抑制時に空を返すと通常 OnBoot に落ちる仕様を利用。OnBoot が出ない経路でも間隔が戻らないよう aitalkinterval=420 を併せて設定）。
  - On_otherghostname（NOTIFY）は一覧を astaroth_og_present に保持するだけの記録用ハンドラとして実装（yaya_base が ID に `On_` を補うことを shiori3.dic line 493 で確認済み）。
  - 名前照合はゴースト名／本体側名の両キー方式。実物 descript.txt で再確認した確定キーのみ接続：．さくら（．さくら／さくら）、S the Skeleton（S the Skeleton／RYS-0825）、荒沢さん（荒沢さん／めのう）。**猫刻・みっしー＆まこぴー・偽春菜は原稿の残課題に従い未接続**（台詞プール OGTalkNekotoke / OGTalkMisshi は収録済みで、キーが確定したら OGSpecificCode へ照合行を足すだけで有効化できる）。
  - 頻度抑制は原稿案をそのまま実装：相手ごとの初回フラグ（astaroth_og_greeted）、全体クールダウン600秒（astaroth_og_lasttime、GETSECCOUNT 差分）、Closed は挨拶済みの相手のみ・見送り時にフラグ解除＋クールダウン更新、A1 は誰にも挨拶していない時だけ（astaroth_og_ever）。汎用の「来た」は A2 と A5（眺める）を半々で振り分け。
  - 干渉確認：system 辞書の aya_lilith は system/_loading_order.txt 先頭行が `# dicdir, aya_lilith` で無効化されており（AYL_OnBoot 等があっても平名 OnBoot が実機で動いているのが証左）、AYL_ へのイベント変換は働かない。yaya_base に OnOtherGhost*/OnInstall* の SHIORI3EV ハンドラは無いことも grep で確認済み。
- **`dic/normal/astaroth_install.dic`**（インストール時、全16本相当）:
  - OnInstallBegin=汎用2本、URL 経由は OnURLDropping=汎用2本、OnURLDropped=無言（直後に Begin が来るため）、OnURLDropFailure=3-3。
  - 完了は OnInstallCompleteEx を正とし、Reference0 を C_BYTE1 で分割して識別子分岐（ghost/shell/balloon/plugin/その他）。旧 OnInstallComplete も同じ INCompleteMain に委譲。複数同時の Ex では短い橋渡し台詞1本に留め（**この1本のみ原稿外の実装時追加**。原稿メモの「どちらか一方を短くする」設計に基づく）、総括は OnInstallCompleteAll の 2-6 に任せる。
  - OnInstallFailure は artificial のみ 3-2、他理由は全て 3-1 に集約。OnInstallRefuse=4-1/4-2 のプール、OnInstallReroute=無言。
  - OnFileDrop2 は 4-3＋代替案のプールで応答し、末尾 \e の直前に `\![execute,dropdefault,file,Reference0]` を差し込んで本体の既定処理（ビューア等）も止めない（タグ書式は UKADOC で裏取り：Reference0 をそのまま渡してよい）。
- 登録・配信：`dic/normal/_loading_order.txt` に正書式で2行追加（全8行、書式違反0件を検証）。ビルドツリー⇔WSL 配信フォルダで MD5 一致（otherghost: 85e18821…、install: 1e79219a…、loading_order: 5176118d…）。`gen_update_file.py` で updates2.dau 再生成（91レコード、9,520 bytes）、全レコード再計算で不一致0・未収録0。今回の配信差分は3件（新規辞書2＋_loading_order.txt）。
- nar：v2.7 として再ビルド（`zip -D`、91エントリ＝v2.6 の89＋新規辞書2、削除0）。`astaroth.nar` 差し替え＋ `astaroth_v2.7_backup.nar` 保存、いずれも 9,961,637 bytes。zip 読み戻しで3ファイルの MD5 一致と _loading_order 書式を確認。両原稿の状態表記も「実装済み」に更新済み。
- 実機確認手順（未実施）：(1) アスタロト側が SSTP NOTIFY（Event: OnAstarothUpdateRequest）でネットワーク更新を起動し、差分3件を取り込む（更新報告トークで件数が出るはず）。(2) 他のゴースト（．さくら / S the Skeleton / 荒沢さん等）を横に呼ぶと個別反応 or 汎用挨拶が出ること、帰すと見送りが出ること。(3) 適当な nar をゴーストへ D&D すると開始→完了の台詞が出ること、画像ファイル等を D&D すると 4-3 の台詞と共にビューアが開くこと。

## 追記7（2026-11-03 他ゴースト言及の不具合修正：「追加で呼ぶ」で反応しない問題 / nar v2.8）

- 現象：ユーザーが SSP の「追加で呼ぶ」で S the Skeleton をアスタロトの隣に並べても、反応トークが出なかった。一方、SSTP NOTIFY で OnOtherGhostBooted（未知のゴースト名入り）を合成送信すると汎用挨拶が正しく返ったため、辞書の読み込みと Booted ハンドラ自体は正常と切り分け済み。
- 原因（UKADOC「SHIORI Event リスト」で確定）：**OnOtherGhostBooted は呼び出し側には配送されない**。仕様文に「呼び出し側に OnGhostCallComplete が発生するのと同じタイミングで、無関係なゴーストに発生する」と明記されており、Booted の宛先はあくまで傍観者の第三者ゴースト。自分のメニューから「追加で呼ぶ」をした場合、アスタロトは呼び出し側なので、来るのは **OnGhostCalling**（呼び出し指示の時点）と **OnGhostCallComplete**（相手の起動スクリプト完了後）の2つで、v2.7 の辞書にはこの両ハンドラが無かった。
- 仕様確認の要点：
  - OnGhostCalling: Ref0=呼ぶ相手の本体側名 / Ref1=manual（手動）か automatic（システム） / Ref2=呼ぶ相手のゴースト名 / Ref3=パス。相手はまだ起動していない。
  - OnGhostCallComplete: Ref0=呼ばれたゴーストの本体側名 / Ref1=相手の起動時スクリプト / Ref2=呼ばれたゴーストの名前 / Ref7=相手のシェル名。**Reference の並びは OnOtherGhostBooted と同一**。
- 修正（`dic/normal/astaroth_otherghost.dic` のみ）：
  1. **OnGhostCallComplete ハンドラを追加**し、`OGReact('booted', reference[2], reference[0])` で既存の挨拶本体を共用。名前照合（両キー方式）・個別反応（B）・頻度抑制がそのまま効く。
  2. **OnGhostCalling ハンドラも追加**したが無言（'' を返す）。相手の起動完了前に喋ると相手の起動トークへ先行・競合し、呼び出しが取り消された場合に挨拶だけ残るため、反応は CallComplete に一本化する設計。
  3. **抑制状態のリセット（今回限りの措置）**：抑制系の状態変数を旧名から _v2 付きへ改名（astaroth_og_greeted_v2 / astaroth_og_lasttime_v2 / astaroth_og_ever_v2 / astaroth_og_lastname_v2）。合成テストでユーザー実機側に立ってしまった旧変数の挨拶済みフラグ・クールダウンを引き継がないため。辞書内のコメントにも「恒常仕様ではなく今回限り」と明記した。記録専用の astaroth_og_present は抑制系でないため改名対象外。Booted/Changed/Closed/Vanished/Called の既存挙動は変更なし。
- 配信反映：ビルドツリー⇔WSL 配信フォルダで MD5 一致（astaroth_otherghost.dic：新 3975abd88fb1a8adb7dff0bad22485b4、旧 85e18821f572430cd4a2193d3938e8c2）。`gen_update_file.py` で updates2.dau 再生成（91レコード、9,520 bytes）、全レコード再計算で不一致0・未収録0を検証。今回の配信差分は astaroth_otherghost.dic の1件のみ。
- nar：v2.8 として再ビルド（`zip -D`、91エントリ＝v2.7 と同一集合、内容差分は astaroth_otherghost.dic のみ）。`astaroth.nar` 差し替え＋ `astaroth_v2.8_backup.nar` 保存、いずれも 9,962,693 bytes。zip 読み戻しで同辞書の MD5 一致と _loading_order.txt の書式違反0件を確認。
- 実機での再確認手順（未実施）：(1) SSTP NOTIFY（Event: OnAstarothUpdateRequest）でネットワーク更新を起動し、差分1件を取り込む（変数リセット込みなので、更新直後は抑制が素の状態に戻っている）。(2) アスタロトのメニューから「追加で呼ぶ」で S the Skeleton を呼ぶ → 相手の起動トーク完了後に、B4（骸骨への個別反応）が出れば修正成功。変数リセットのおかげで、前回の合成テストで立った挨拶済み扱いにはならない。(3) ついでに、他ゴーストのメニューやトレイから第三者を呼んだ場合（傍観経路＝Booted）でも従来通り反応すること、帰すと見送り（A4）が出ることも確認できるとなお良い。

## 追記8（2026-11-03 シェル拡充第一弾：アスタロトのポーズ4種＋表情違い4枚 / nar v2.9）

原稿 SHELL_EXPANSION.md §1.1／§1.3／§2 に基づく第一弾（アスタロト先行はユーザー決定）。ポーズ候補→ユーザー選択→表情差分生成→シェル化→辞書割り当て→ネットワーク更新配信まで実施。

- **土台の選択（ユーザー確定）**：pose6＝pose6_seedA（seed 20261101、腕を下げて前で手を重ねる）、pose7＝pose7_fixA3（seed 20262102、両掌を胸前でかざし少し俯く・柔らかい心配顔）、pose8＝pose8_seedB（seed 98101、本を両手で抱える hug 版）、pose9＝pose9_seedA（seed 20261101、腕組み）。
- **pose9 の表情条件と結末**：候補Cの「偉そうな顔（半眼気味の見下し）」への接近が条件だったが、C 系統は「腕組み＋イブニングドレス」の結び付きでスリット入りになりやすく、修正候補3枚ともスリット除去に失敗。ユーザーの了承で「スリットなしの seedA を土台に、表情差分の制作時に C 寄りへ寄せ直す」方針へ変更した。表情生成の際、偉そう指定を強めた基番候補（pose9h、生成スクリプト work/gen_pose_expr.py、src は work/pose_expr_raw/ に保管）も作ったが、やはり深いスリットが出て「スリットなし厳守」の条件を満たさず不採用。基番9 は seedA をそのまま採用（元々軽い見下し顔）。偉そうな表情の強化は、将来の体×顔 element 合成（二段構え）に持ち越し。
- **新 surface（8枚）**：
  - 6：手を重ねる（630×1216。裾のトレーンが広がるため幅広）
  - 7：手を合わせ俯く（478×1216）
  - 8：本を抱える（478×1216）
  - 9：腕組み（478×1216）
  - 46：6＋笑顔（seed 20261101、478×1216）
  - 47：7＋目閉じ（seed 20262102、478×1216）
  - 48：8＋笑顔（seed 98101、496×1216）
  - 49：9＋通常・穏やかな顔（seed 20261101、478×1216。生成で半袖ドレスになったが衣装細部の差異として許容）
  - 表情違いは原稿 §1.3 の最小構成どおり各ポーズ1種（当初案の「最大2種」からは絞った）。生成は work/gen_pose_expr.py（WSL 実行、土台と同シード・同ポーズ指定で表情指定だけ差し替え）。採用元絵は src_images/astaroth_pose{6,7,8,9,46,47,48,49}_seed*.png。キーイングは finalize_expr.py の既存工程（影は緑優位ピクセルとして既存の緑優位減衰で除去でき、暗背景プレビューで残存なしを確認。透明画素 RGB=(0,255,0) 統一、.pna はアルファと完全一致を検証）。
- **surfaces.txt の実測値**（全ポーズ、暗背景プレビュー＋50pxグリッドの目視実測。surface0 の流用なし）：
  - 6：Head 190,78,368,282／Face 205,148,345,278／Bust 185,385,450,505
  - 7：Head 92,82,292,338／Face 112,200,268,332／Bust 65,437,325,557（顔は左寄り）
  - 8：Head 132,70,318,268／Face 152,148,298,262／Bust 125,365,340,490
  - 9：Head 126,76,324,262／Face 146,182,304,256／Bust 110,361,375,481
  - 46：Head 140,80,300,264／Face 160,156,280,258／Bust 120,363,375,483
  - 47：Head 105,98,262,304／Face 130,182,240,298／Bust 85,403,330,523（深く俯くため顔が低く左寄り）
  - 48：Head 152,72,324,254／Face 172,146,304,248／Bust 130,353,360,473
  - 49：Head 130,78,315,258／Face 150,160,295,252／Bust 115,357,370,477
  - バルーンは従来どおりシェル全体の offset（0,0）のまま（ポーズ別の balloonoffset は付けていない。既存 surface 間でも顔位置はばらついており同方式で運用中）。
  - 実測の試行錯誤：肌色クラスタ方式はオフショルダーの胸元・肩の肌と顔が連結して失敗（surface0 の既存定義と大きくずれた）。最終的にグリッド目視に切り替え、surface0 の既存定義（Head 150,60,320,255 等）と矛盾しないことを確認したうえで全ポーズに適用した。試作スクリプトは work/measure_surface.py に残置（幅プロファイル版。顔検出は未完なので次回はグリッド目視が正）。
- **辞書割り当て（astaroth_talk.dic v3.1）**：台詞本文は無変更のまま、アスタロト側のサーフェス指定を計31箇所で差し替え（6×9／7×6／8×3／9×6／46×3／47×2／48×1／49×1）。方針：本の話→8／48、偉そう・命令・小言→9、心配・気遣い→7、穏やかな独白・解説→6、目閉じ系→47、穏やかな腕組み→49。トーク100本の本数・選択ロジック（間隔420秒／配分／直近5件履歴回避）は無変更。他辞書は未変更。辞書冒頭のサーフェス対応コメントにポーズ分を追記した。
- **配信**：変更18ファイル（新 surface の png/pna 16件＋surfaces.txt＋astaroth_talk.dic）を WSL 配信フォルダへコピーし MD5 全件一致を確認。`gen_update_file.py` で updates2.dau を再生成（107レコード、11,088 bytes）し、別途全レコードを再計算して不一致0を検証。
- **nar**：v2.9 として再ビルド（`zip -D`、107エントリ＝v2.8 の91＋新 surface 16）。`astaroth.nar` 差し替え＋ `astaroth_v2.9_backup.nar` 保存、いずれも 14,388,009 bytes、MD5 c0ead39ad4421371aef8708a4521e4bb。zip 読み戻し検証済み（testzip 正常、新 surface 16件の収録確認）。_loading_order.txt は今回未変更（辞書の追加・削除なし）。
- **実機確認手順（未実施、ユーザー側）**：(1) SSTP NOTIFY（Event: OnAstarothUpdateRequest、WSL の ~/sstp_updaterequest.py）でネットワーク更新を起動し、差分18件を取り込む（更新報告トークで件数が出る）。(2) SSTP NOTIFY（Event: OnFurfurTalkTest、WSL の ~/sstp_talktest.py）でランダムトークを繰り返し呼び、本・知識系の台詞で pose8、偉そうな台詞で pose9、気遣い系で pose7、穏やかな独白で pose6／46 が出ることを確認する（履歴回避で直近5本は重複しない。100本中31箇所がポーズ指定なので数回に1回はポーズが出る計算）。(3) ポーズ表示時に当たり判定（頭・顔・胸へのマウス反応）とバルーン位置が大きくずれていないかも併せて見る。

## 追記9（2026-11-03 インストール総括台詞の不具合修正：1件でも「まとめて全部」が出る問題 / nar v2.10）

ユーザーの実機報告で判明：バルーンを1件だけインストールしたときにも、複数インストール用の総括台詞「まとめて全部、入り終わったわ。」（OnInstallCompleteAll に割り当てた 2-6）が出てしまう。対象は `astaroth_install.dic` のみ。

- **仕様の再確認（UKADOC「SHIORIイベントリスト」Install Events）**：OnInstallCompleteAll は「Occurs last, after OnInstallComplete/Ex, when all installations have been completed successfully, such as when multiple NARs have been dragged and dropped」。Reference0/1/2 は CompleteEx と同型（識別子／名前／場所、複数ならバイト値1区切り）。文面は複数 nar を例示するが、現行 SSP の実機挙動では1件のセッションでも最後に必ず発生する（＝セッション終了の合図）ことをユーザーのテストが示した。よって「All が来た＝複数」とは扱えない。
- **修正方針（セッション内カウント）**：新規にユーティリティ INSessionOpen／INCountUp／INSessionTotal／INSessionClose と状態変数 `astaroth_in_session`／`astaroth_in_count`／`astaroth_in_lasttime`（このファイル内でのみ管理）を追加。
  - OnInstallBegin で INSessionOpen：進行中セッションがある間はリセットしない（Begin がアーカイブごとに発生しても数え直さないため。当初の想定「Begin のたびにリセット」だと、2ファイル D&D で Begin が2回来た場合に最後の1件分しか数えられない）。前セッションが総括まで至らず放置された場合は、最終活動（GETSECCOUNT）から600秒超で古いセッションとして破棄する。
  - OnInstallCompleteEx／OnInstallComplete で INCountUp(reference[0])：そのイベントが運んだ識別子の数（SPLIT の要素数＝完了した物の数）を加算。失敗・拒否では Complete 系自体が来ないので「失敗は数えない」が自然に成立する（Failure／Refuse／Reroute のハンドラは数に触らない）。
  - OnInstallCompleteAll：総件数 ＝ セッション内カウントと、CompleteAll 自身の Reference0 の識別子数のうち大きい方（どちらか一方の取りこぼし対策）。2件以上なら従来の 2-6 を喋り、1件なら無言（種別ごとの完了台詞 2-1〜2-5 で締める）。判定後に INSessionClose でセッションを閉じる。
  - これにより、1つの nar に複数同梱（ghost＋balloon 等、CompleteEx の Ref0 が2件）の場合も2件として総括が出る（従来設計どおり）。INCompleteMain の橋渡し台詞は無変更。
- **検証**：波括弧バランス 45/45、新規関数名が他辞書と重複しないことを確認。YAYA の実機パース確認は未実施（次回の実機テストで兼ねる）。
- **配信**：変更は astaroth_install.dic の1ファイルのみ。WSL 配信フォルダへコピーし MD5 一致（d50a50d820ddc1590e926c96c3f71dea）。`gen_update_file.py` で updates2.dau を再生成（107レコード、11,088 bytes）し、別途パースして全レコードの MD5 再計算で不一致0・未収録0を検証。
- **nar**：v2.10 として再ビルド（`zip -D`、107エントリ＝v2.9 と同一集合、内容差分は astaroth_install.dic のみ）。`astaroth.nar` 差し替え＋ `astaroth_v2.10_backup.nar` 保存、いずれも 14,388,950 bytes、MD5 29342fdc268ce20860024915081cf814。zip 読み戻し検証済み（testzip 正常、収録 astaroth_install.dic の MD5 がビルドツリーと一致、_loading_order.txt は全行 `dic, ファイル名, UTF-8` の正書式）。
- **実機確認手順（未実施、ユーザー側）**：(1) SSTP NOTIFY（Event: OnAstarothUpdateRequest）でネットワーク更新を起動し、差分1件を取り込む。(2) バルーン単体を1件だけ D&D する → 開始台詞と 2-3（バルーン）の台詞だけが出て、総括「まとめて全部、入り終わったわ。」が出ないことを確認。(3) nar を2件まとめて D&D する → 個別完了の後に総括 2-6 が出ることを確認。(4) ついでに、失敗するアーカイブ単体 → 失敗台詞のみで総括が出ないこと、も見られるとよい。

## 追記10: v2.10 辞書破損インシデントと復旧、総括修正の最小変更での再適用（2026-11-03 夜、現行 v2.12）

- **発生**：v2.10（astaroth_install.dic のセッション件数管理追加）配信後、ゴーストが全イベント無応答（SSTP 204）になり、再起動では SSP が「致命的なエラー」を表示。インストール時に限らず辞書全体が読み込めていなかった。
- **原因の切り分け**：破損版と正常版の全量 diff・波括弧バランス（45/45）・関数名の重複・文字コード（UTF-8／LF）を全て確認したが、静的に特定できる欠陥はなし。正常動作中の他辞書で実績のある構文（ISVAR、TOINT(GETSECCOUNT)、SPLIT+C_BYTE1、ARRAYSIZE、_argv）と v2.10 の差分は、**「代入も return もしない裸の関数呼び出し文」（INSessionOpen／INSessionClose の単独行呼び出し）**が唯一の未実績構文であり、最有力候補として記録する（確定ではない）。
- **復旧**：配信側を正常版へ巻き戻したが、ユーザーのネットワーク更新は updates2.dau のみ取得して「差分なし」となり、壊れたファイルが入り直らなかった。SSP 側の更新台帳と実ファイルの不整合が原因と見られる。上書きインストールでも直らず、最終的に**ユーザーがゴーストフォルダを削除し、復旧用 nar（v2.9 相当）で入れ直して復旧**した。以後、辞書破損級の復旧は「フォルダ削除＋nar 入れ直し」を正規手順とする。
- **再適用（v2.12）**：総括の出し分けを、セッション状態を持たない最小変更で実装し直した。OnInstallCompleteAll の中だけで Reference0 を `ARRAYSIZE(SPLIT(reference[0], C_BYTE1))` で数え（実績構文の代入文のみ）、2件以上で総括、1件・空では無言。新規関数・新規構文は一切なし。
- **検証（合成テスト、全て想定どおり）**：talktest=200 で台詞返却／CompleteAll・識別子1件=204（無言）／2件=200 で総括台詞／空=204。ネットワーク更新フック経由で配信し、取得ログ（install.dic）も確認。
- **nar**：v2.12 として再ビルド（`zip -D`、107エントリ、14,388,136 bytes）。`astaroth.nar` 差し替え＋ `astaroth_v2.12_backup.nar` 保存。v2.11 相当の復旧 nar は astaroth_v2.11_recovery_backup.nar として保存済み。v2.10 は破損版として使用禁止（記録用にのみ保持）。
- **実機確認（完了）**：2026-11-03 20:10、ユーザーがゴーストのインストールとバルーンだけのインストールの両方を実機で行い、どちらも問題なくできたと報告。これで本件は解決済み。

## 追記11: GitHub 版管理の開始（2026-11-03 夜）

- v2.10 の手戻りを教訓に、プロジェクトを Git 管理下に置いた。リモートは非公開リポジトリ **FumiakiKob/astaroth-ghost**（ユーザーが「非公開なら音声も問題ない」と判断し、音声 MP3 も含む）。
- 構成：辞書・原稿・設計書・ビルドツリーを追跡。画像（png/pna）と音声（mp3/wav）は Git LFS（72 objects、約13MB）。`*.nar` と `work/` の作業スクラッチ（台本の .py/.md を除く）と `src_images/` は .gitignore で除外。
- 初回コミット c616a0d にタグ **v2.12**（nar v2.12 相当）。push 済みで、新規 clone＋`git lfs pull` で画像・音声の実体が復元できること、辞書の MD5 一致まで検証済み。
- 認証の経緯と制約：gh の標準ログインはスコープが広く（repo＋read:org で所属 organization に届き得る）ユーザーが懸念したため中止。SSH はこの VM の出口が塞がれており deploy key は使えない。最終的に、**リポジトリ単独に絞った fine-grained PAT（Contents RW、30日）をユーザーが発行し、一時利用で push**した。トークンはアスタロト側に一切保存していないため、今後の push のたびに再発行・再手渡しが必要。
- 運用ルール：辞書を配信する前にコミットし、nar を作るたびにバージョンタグを打つ。壊れたら git から該当ファイルを取り戻す。

## 追記12: push 経路を deploy key＋トンネル SSH へ移行（2026-11-03 夜）

- ユーザーの選択により、認証を PAT 一時利用から **リポジトリ単独の deploy key** へ移行した（ユーザーが再登録、write 許可あり）。
- この VM からの生 SSH は出口の HTTP プロキシ（CONNECT 専用）に切られるため、ssh.github.com:443 へ CONNECT トンネルで接続する。ヘルパーは `~/workspace/scripts/ssh-connect-proxy.py`（https_proxy 環境変数からプロキシ認証を組み立てる ProxyCommand）。
- この実行環境の ssh は `~/.ssh/config` を既定で読まなかったため、設定はリポジトリ側に埋めた：origin = `ssh://git@ssh.github.com:443/FumiakiKob/astaroth-ghost.git`、`core.sshCommand` に ProxyCommand と鍵（~/.ssh/id_ed25519）を指定。
- 検証：deploy key の認証応答（リポジトリ名入りの挨拶）、ls-remote、push dry-run、**LFS push dry-run（SSH 認証経由）**まで全て成功。以後の push はトークンの手渡しなしでアスタロト側から実行できる。

## 追記13: シェル拡充フルフル分：ポーズ4種＋表情違い4枚（2026-11-03 夜、nar v2.13）

原稿 SHELL_EXPANSION.md §1.2／§1.3／§2 に基づくフルフル分（16〜19＋56〜59）。ユーザーの委任（「手が空いているときに進め、まとめて後で確認」）で、候補選択も含めてアスタロト側で実施した。確認用コンタクトシートは work/furfur_pose_preview.png。

- **制作方法**：アスタロト第一弾と同じブループリント（CottonAnima base1、832×1216、30step/CFG4/er_sde、緑背景）。キャラ固定仕様は gen_furfur_expr.py のものを流用し、ポーズ指定だけ差し替えた（work/gen_furfur_poses.py）。ポーズごとに3シードの候補を生成し、容姿の一貫性・ポーズ再現度・キーイング適性（影や浮遊物の少なさ）で採用を決定。表情違いは採用土台と同シード・同ポーズ指定で表情だけ差し替えて生成（work/gen_furfur_pose_expr.py）。
- **採用土台**：16＝seed16101（身を乗り出す。1031案は足元の影が残るため不採用）、17＝seed17102（両手を広げて喜ぶ。ドレス仕様が最も正確）、18＝seed1031（拗ねてそっぽ。湯気マークはキーイングの成分整理で除去）、19＝seed1031（両手を合わせてお願い。足元の影は背景として綺麗に抜けた）。
- **新 surface（8枚）**：
  - 16：身を乗り出す（821×1216、seed 16101）
  - 17：両手を広げて喜ぶ（822×1216、seed 17102）
  - 18：拗ねてそっぽ（684×1216、seed 1031）
  - 19：両手を合わせてお願い（825×1216、seed 1031）
  - 56：16＋照れ（819×1216、seed 16101。生成でフリル付き靴下が付いたが衣装細部の差異として許容）
  - 57：17＋目閉じ（833×1216、seed 17102）
  - 58：18＋驚き（679×1216、seed 1031。驚きマークは成分整理で除去）
  - 59：19＋笑顔（829×1216、seed 1031）
  - キーイングは finalize_furfur.py と同一処理（フルフル専用 ramp＋成分整理、work/finalize_furfur_poses.py）。配置はポーズごとに個別（H=1216、下端は既存フルフル surface と同じ y=1211。ただし 16／56 は上端がはみ出すため全体を収めることを優先し下端 1215）。全枚で .pna＝アルファ完全一致、四隅 alpha=0、透明画素 RGB=(0,255,0) を検証。
- **surfaces.txt の実測値**（全ポーズ、暗背景プレビュー＋50pxグリッドの目視実測。surface10 の流用なし）：
  - 16：Head 215,120,485,365／Face 265,215,395,360／Bust 270,430,435,565
  - 17：Head 265,105,505,300／Face 300,185,455,295／Bust 275,360,485,490
  - 18：Head 200,40,565,255／Face 330,150,480,250／Bust 295,385,510,520
  - 19：Head 225,55,610,360／Face 265,215,510,355／Bust 255,450,540,620
  - 56：Head 225,105,495,365／Face 255,255,390,360／Bust 270,435,430,560
  - 57：Head 295,130,550,300／Face 320,235,490,300／Bust 305,385,520,500
  - 58：Head 215,45,560,250／Face 335,145,475,245／Bust 285,395,500,515
  - 59：Head 235,100,610,345／Face 280,230,505,340／Bust 265,440,530,600
  - バルーンは従来どおりシェル全体の offset（0,0）のまま。
- **辞書割り当て（astaroth_talk.dic v3.2）**：台詞本文は無変更のまま、フルフル側のサーフェス指定を計20箇所で差し替え（16×4／17×6／18×4／19×2／56×2／58×1／59×1。57 は「明らかに合う」台詞がなかったため未割り当て）。方針：マスターへ迫る・気遣いの押し→16（ドキドキの有無、水分、笑顔点検、肩もみ）、喜び・応援・自己紹介→17（応援二人分、デザート係、自己紹介、雷は拍手、朝の目覚まし、空に勝った）、拗ね→18（26番目ネタの回収、独り占め、たまにって何、ドレス交換のぶー）、夢の約束→19（約束の蒸し返し、夢で待ってる）、恋の告白の押し→56（声が高くなる、まとめて大好き）、振り向きの驚き→58（独り言がバレた）、おねだりの笑顔→59（大好きおかわり）。選択ロジック・他辞書は無変更。辞書冒頭のサーフェス対応コメントにフルフルポーズ分を追記（v3.1 の前例どおり）。
- **配信**：2段階で実施し、各段階で取得ログと talktest を確認した。(1) シェル17ファイル（新 surface 16件＋surfaces.txt）を配信し、updates2.dau（123レコード）再生成→フックで更新起動→SSP が全17ファイルを取得、talktest=200。(2) astaroth_talk.dic を配信（MD5 一致）→同様に取得確認→talktest 12回すべて 200 で、返却スクリプトに新ポーズ（\s[19] 夢で待ってる／\s[17] 雷は拍手／\s[16] 肩もみ）の出現を確認。
- **nar**：v2.13 として再ビルド（`zip -D`、123エントリ＝v2.12 の107＋新 surface 16）。`astaroth.nar` 差し替え＋ `astaroth_v2.13_backup.nar` 保存、いずれも 20,037,545 bytes。zip 読み戻し検証済み（testzip 正常、変更18ファイルの MD5 がビルドツリーと一致）。
- **git**：コミット 7d02b74＋タグ v2.13 を push 済み。
- **実機確認（後日、ユーザー側）**：コンタクトシート（work/furfur_pose_preview.png）での見た目確認と、ランダムトークでポーズが出た際の当たり判定・バルーン位置の確認。問題があれば該当 surface の差し替えで対応する。

## 追記14: シェル拡充第二弾：座りポーズ2枚（2026-11-03 夜、nar v2.14）

原稿 SHELL_EXPANSION.md §1.1／§1.2／§2 に基づく座りポーズ（20／21）。バッチ1と同じくユーザーの委任（「手が空いているときに進め、まとめて後で確認」）で、候補選択も含めてアスタロト側で実施した。確認用コンタクトシートは work/sitting_pose_preview.png。

- **制作方法**：同じブループリント（CottonAnima base1、832×1216、30step/CFG4/er_sde、緑背景）。キャラ固定仕様は gen_poses.py（アスタロト）／gen_furfur_poses.py（フルフル）を流用し、ポーズ指定だけ座りに差し替えた（work/gen_sitting.py）。椅子を描くため NEG から furniture／sitting を外し、簡素な木製の椅子を指定。アスタロトは当初3シード全てに床影が出たため、影消しを強化して3シード追加生成した（work/gen_sitting2.py）。
- **採用土台**：
  - 20＝seed 201103（椅子に腰掛け膝を揃える。オフショルダーのドレス仕様が最も正確で、影も最小）
  - 21＝seed 21101（座って足をぶらつかせる。足が座面から垂れて揺れる動きが出た唯一の候補。基準シード1031案は足が床に着いており不採用）
- **新 surface（2枚）**：
  - 20：アスタロト座り（762×1216、seed 201103）
  - 21：フルフル座り（792×1216、seed 21101）
  - キーイングは二人分それぞれの既存 finalize と同一処理（work/finalize_sitting.py）。配置は H=1216、幅は bbox＋マージンの可変幅でセンタリングし、椅子の脚下端を既存立ち絵の接地ライン（20=1212／21=1211）に合わせた。全枚で .pna＝アルファ完全一致、四隅 alpha=0、透明画素 RGB=(0,255,0) を検証。床影は成分整理で除去できた。
  - 21 の留意点：元絵のキラキラ装飾のうち髪に密着した小さな星型が数個残留した。髪の描線と機械的に分離できず、輪郭を壊すリスクを避けて残置した（髪飾り程度の見た目。実機確認時に気になれば手作業マスクで除去する）。
- **surfaces.txt の実測値**（暗背景プレビュー＋50pxグリッドの目視実測。既存値の流用なし）：
  - 20：Head 210,110,500,340／Face 290,235,450,335／Bust 280,370,510,520
  - 21：Head 250,30,665,300／Face 385,180,550,290／Bust 335,340,565,505
  - バルーンは従来どおりシェル全体の offset（0,0）のまま。
- **辞書割り当て（astaroth_talk.dic v3.3）**：台詞本文は無変更のまま、サーフェス指定を計2箇所だけ差し替えた（20×1／21×1）。方針：夜の静かな思考（「夜は頭の使う時間よ」\s[6]→\s[20]）、夜のまったりした掛け合い（「夜って、誰かのことを考える時間」フルフル側 \s[14]→\s[21]）。読書独白は本ポーズ8が最適のため変更なし。選択ロジック・他辞書は無変更。辞書冒頭のサーフェス対応コメントに座り分を追記（前例どおり）。
- **配信**：2段階で実施し、各段階で取得ログと talktest を確認した。(1) シェル5ファイル（新 surface 4件＋surfaces.txt）を配信し、updates2.dau（127レコード）再生成→フックで更新起動→SSP が全5ファイルを取得、talktest=200。(2) astaroth_talk.dic を配信（MD5 一致）→同様に取得確認→talktest 20回すべて 200（204 はゼロ）で、返却スクリプトに \s[20]（夜は頭の使う時間よ）と \s[21]（夜って、誰かのことを考える時間）の出現をそれぞれ確認。
- **nar**：v2.14 として再ビルド（`zip -D`、127エントリ＝v2.13 の123＋新 surface 4）。`astaroth.nar` 差し替え＋ `astaroth_v2.14_backup.nar` 保存、いずれも 21,708,089 bytes。zip 読み戻し検証済み（testzip 正常、追加・変更6ファイルの MD5 がビルドツリーと一致、削除0）。
- **git**：コミット 0abfd57＋タグ v2.14 を push 済み。
- **実機確認（後日、ユーザー側）**：コンタクトシート（work/sitting_pose_preview.png）での見た目確認と、夜帯のランダムトークで座りポーズが出た際の当たり判定・バルーン位置・接地位置の確認。21 の髪の星型が気になる場合は差し替えで対応する。

## 追記15: シェル拡充バッチ3（最終便）：不在看板5枚＋状態管理＋自動立て替え（2026-11-03 夜、nar v2.15）

原稿 SHELL_EXPANSION.md §3 と GHOST_RESEARCH.md §6.4 の推奨構成に基づく不在看板（26〜30）。バッチ1・2と同じくユーザーの委任（「手が空いているときに進め、まとめて後で確認」）で実施した。確認用コンタクトシートは work/sign_preview.png。

- **看板 surface（5枚、全て 478×1216）**：土台は共通の木製立て看板。文字なしの看板だけを ComfyUI で生成（work/gen_sign.py、CottonAnima base1、832×1216、30step/CFG4/er_sde、緑背景、3シードから seed26101 を採用＝影なし・無地でキーイング適性が最良）。キーイングは finalize_expr.py と同一方式（work/finalize_sign.py）で、高さ1000pxにスケールし下端を既存シェルの接地ライン y=1211 に配置。**文字は AI に描かせず、板の矩形（実測 53,254〜423,1016）へ PIL で後入れ**した（Noto Serif CJK Bold、濃茶、タイトルは板幅に自動調整、サブは1行）。
  - 26 入浴中／「覗くと業火で丸焼きよ」
  - 27 外出中／「留守は任せなさい」
  - 28 勉強中／「邪魔をすると祟るわよ」
  - 29 就寝中／「夢の中では静かにね」
  - 30 お留守番中（フルフル版）／「早く帰ってきてねー！」
  - surfaces.txt には板部分のみの当たり判定（collision0,53,254,423,1016,Sign）を全看板共通で登録。予約コメントに 26〜30 の実装済みと、3000番台＝パーツ帯予約（GHOST_RESEARCH §6.1）を追記。全枚で .pna＝アルファ完全一致・四隅 alpha=0 を検証。
- **辞書（新規 astaroth_signboard.dic、_loading_order.txt に正書式で登録）**：状態変数 `astaroth_signboard`（0／26〜30、YAYA の保存対象なので SSP 終了後も残る）で一元管理する。
  - `OnAstarothSignboard`（SSTP NOTIFY フック、Reference0=番号／0=しまう／他は無視）→ SignboardSet／SignboardClear。立て替え時は「一言→看板表示＋フルフル非表示（\1\s[-1]）」の順で返し、しまう時は種別ごとの復帰トーク（SignboardReturnTalk、TalkReturn 規約）を返す。
  - `OnSurfaceRestore`：看板中なら看板 surface とフルフル非表示を無言で再適用（S the Skeleton の就寝モード再適用と同型）。看板なしでは空を返す。
  - ランダムトーク差し替え：astaroth_talk.dic の RandomTalk 入口にゲートを追加し、看板中は通常選出（履歴処理を含む従来本体は else 側に無変更で温存）ではなく SignboardMutter（種別ごとに2本の呟きプールへ振り分け）を返すようにした。
  - 起動時吸収：astaroth_bootend.dic の OnBoot で SignboardBootCheck を先に呼び、看板状態が残っていれば復帰トークを返して通常起動トークを置き換える（空なら従来どおり OnBootTalk）。
  - 規律：新規関数の呼び出し結果は全て代入文で受け、裸の呼び出し文なし。全辞書の波括弧バランスと新規関数名の重複なしを確認。
- **自動立て替え（WSL systemd timer）**：送信スクリプト ~/sstp_signboard.py（引数=番号、sstp_updaterequest.py と同型）を新設し、timer 2本を設置・有効化した。
  - astaroth-signboard-bath.timer：毎日 23:00 → 看板26（入浴中）
  - astaroth-signboard-sleep.timer：毎日 23:25 → 看板29（就寝中）
  - サービス実地起動でも発火を確認（journal に NOTIFY と応答スクリプト）。
  - **割り切り**：ユーザーは 8 時に PC を落として出発し、就寝時に PC をスリープさせるため、PC が落ちている時刻の自動切替は成立しない。27（外出中）は自動化せず、手動スクリプト（`python3 ~/sstp_signboard.py 27`、しまうは `0`）での運用とする。朝の復帰はタイマーではなく OnBoot の吸収（看板が残っていれば復帰トークで通常表示に戻る）で受ける。28（勉強中）・30（お留守番）も手動専用。
  - カスタムメニュー（右クリックからの立て替え）は今回見送り。標準メニューしかない現行構成に OnSakuraMenu を足すとメニュー全体の置き換えになり影響が大きいためで、手動経路は SSTP スクリプトで代替できている。将来 astaroth_menu.dic を作る際の第一候補とする。
- **検証（合成テスト、SSP 実機・全て想定どおり）**：立て替え（26〜30 の5種全てで立て替え一言＋末尾の看板切替タグを確認）／看板中の OnSurfaceRestore→再適用スクリプト／看板中の talktest→呟き（\s[26] の台詞）／しまう（0）→種別ごとの復帰トーク／解除後の talktest→通常トーク／29 を立てた状態での OnBoot→復帰トーク（おはよう）で吸収し以後は通常トーク／看板なしでの OnSurfaceRestore→無応答。異常（204 の誤発・辞書読み込み失敗）はゼロ。
- **配信**：2段階で実施し、各段階で取得ログと talktest=200 を確認した。(1) シェル11ファイル（新 surface 10件＋surfaces.txt）、updates2.dau は137レコード。(2) 辞書4ファイル（astaroth_signboard.dic 新規＋_loading_order.txt＋astaroth_talk.dic＋astaroth_bootend.dic）、同138レコード。全ファイル MD5 一致。
- **nar**：v2.15 として再ビルド（`zip -D`、138エントリ＝v2.14 の127＋新 surface 10＋新辞書1）。`astaroth.nar` 差し替え＋ `astaroth_v2.15_backup.nar` 保存、いずれも 22,586,061 bytes。zip 読み戻し検証済み（testzip 正常、主要7ファイルの MD5 がビルドツリーと一致、_loading_order.txt の書式違反0）。
- **git**：コミット＋タグ v2.15 を push する（本追記の記録コミットとともに行う）。
- **実機確認（後日、ユーザー側）**：コンタクトシート（work/sign_preview.png）での見た目確認と、23:00／23:25 の自動立て替えの実地確認（今夜から発火する）。文面・台詞は全て astaroth_signboard.dic と finalize_sign.py の SIGNS 表に集約してあり、差し替えは該当箇所の書き換えだけで可能。
