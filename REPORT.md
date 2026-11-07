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

## 追記16: つつき・撫で反応の新規実装（2026-11-04、nar v2.16）

ユーザーの指摘（つついたり頭を撫でたりしたときの反応がない）を受けて新規実装。台詞は「原稿チェック不要」の委任によりアスタロト側で執筆した。

- **仕様の裏取り（UKADOC「SHIORI Event リスト」、2026-11-04）**：OnMouseDoubleClick／OnMouseMove ともに Reference0=x座標、1=y座標、3=対象スコープ（本体0／相方1）、4=当たり判定の識別子。OnMouseDoubleClick は Reference5=ボタン（左0／右1）、Reference2=常に0。OnMouseMove は Reference2=ホイール回転量、Reference5=常に0（SSP）。部位名は surfaces.txt の登録名（Head／Face／Bust、看板は Sign）と一致させた。
- **新規辞書 astaroth_touch.dic**（_loading_order.txt に正書式で登録、関数33個）：
  - つつき：OnMouseDoubleClick（左ボタンのみ）。部位（Head／Face／Bust／その他）×対象（アスタロト／フルフル）の8プール、各2〜3本、相手の一言添えあり。Bust は品を保った叱り・呆れに寄せた。クールダウンは対象ごとに5秒（連打抑制、対象別に独立）。
  - 撫で：OnMouseMove で Head 上の往復を検出。片道12px以上の区間を数え、3秒の窓内で向きの反転が3回に達したら発火。クールダウンは対象ごとに20秒。撫で累積回数（対象別、永続）で3段階に変化（段階1=1〜2回／段階2=3〜5回／段階3=6回以上）。アスタロトは「突っぱねる→慣れる→少しだけ許す」、フルフルは最初から喜び、段階ごとに距離が縮まる。各段階2本。
  - **単発クリック（OnMouseClick）には反応を付けない**（意図的な判断）：単発クリックはゴーストを掴むドラッグ操作の開始と区別がつかず、掴むたびに喋ると移動の邪魔になるため。つつきはダブルクリックに寄せた。
  - 看板表示中（astaroth_signboard != 0）は二人とも不在のため全タッチ反応を停止する。
  - 保守フック OnAstarothTouchTest（Reference0='reset'／'pre2'／'pre5'）で状態初期化と段階プリセットが可能（合成テストで進めた段階を実機に残さないため、テスト後に reset で初期状態へ戻した）。
  - 規律：呼び出し結果は全て代入文で受け、裸の呼び出し文なし。波括弧 106/106、全辞書で関数名の重複なし、UTF-8／LF を確認。
- **検証（合成テスト、WSL の ~/sstp_touchtest.py、25項目すべて合格）**：つつきマトリクス8件（部位×対象、想定プールの台詞が返る）／同一対象の連打は 204 で抑制・他対象は独立に発火／右ボタンは無反応／撫では1ストロークで正確に1回だけ発火し段階1〜3（両名とも、pre2・pre5 プリセットで確認）が想定プールの台詞を返す／撫でクールダウン中は無発火／看板26表示中はつつきが無反応になり、解除で復帰／talktest=200（他辞書への影響なし）。
- **配信**：辞書2ファイル（astaroth_touch.dic 新規＋_loading_order.txt）を配信フォルダへコピー（MD5 一致）、updates2.dau 再生成（139レコード）、更新フックで SSP が両ファイルを取得したことをログで確認。
- **nar**：v2.16 として再ビルド（`zip -D`、139エントリ＝v2.15 の138＋新辞書1、22,591,461 bytes）。`astaroth.nar` 差し替え＋ `astaroth_v2.16_backup.nar` 保存。zip 読み戻し検証済み（testzip 正常、touch.dic の MD5 一致、_loading_order.txt の書式違反0）。
- **git**：コミット 37f26f6＋タグ v2.16 を push 済み。
- **実機確認（後日、ユーザー側）**：実際に頭をつつく・撫でる操作での発火感度（特に撫での往復検出の閾値：片道12px／反転3回／窓3秒）の確認。鈍い・敏感すぎる場合は TouchNadeStep の定数を調整する。

## 追記17: 就寝看板が朝も残る問題と、朝の自動解除タイマー追加（2026-11-05）

- **症状**：23:25 に立てた就寝看板（29）が、翌朝になっても立ったまま（ユーザーの実機報告）。
- **原因**：看板を「しまう」側の自動化が存在せず、復帰は辞書の OnBoot 吸収（起動時に看板状態が残っていれば復帰トークで戻す）頼みだった。しかしユーザーの PC は夜間スリープ運用で、朝は「起動」ではなく「復帰」のため OnBoot が発生せず、状態が残り続けた。設計時の見落とし。
- **対応**：WSL に `astaroth-signboard-morning.timer` を新設。平日 07:30／週末 09:00（仮）に `sstp_signboard.py 0` を実行して看板をしまう。`Persistent=true` のため、発火時刻にスリープ中でも復帰直後に実行される。サービス定義は従来の bath／sleep と同形式（oneshot、User=muse）。
- **確認**：導入直後にサービスを手動実行し、立っていた就寝看板が解除されて復帰トーク（「おはよう、貴方。よく眠れた？」）が返ることを実地で確認。talktest も 200。
- **教訓**：状態の後片付けは「次回起動時」ではなく時刻ベースで設計する。スリープ運用では起動イベントは来ない。

## 追記18: 朝の自動解除を毎日7:30に統一（2026-11-05）

- 追記17 で平日 07:30／週末 09:00（仮）としていた自動解除を、ユーザーの指示（週末も7時半でよい）で **毎日 07:30** に統一した。タイマーは `OnCalendar=*-*-* 07:30:00`、`Persistent=true` は維持。次回発火は 2026-11-06 07:30 で表示確認済み。

## 追記19: 右クリックメニュー（カスタムメニュー）とトーク頻度設定の新規実装（2026-11-05、nar v2.17）

ユーザーの決定済み案件（ロードマップの右クリックメニュー自作）。途中で「トーク頻度の設定」の追加要望も入り、同じ便で実装した。台詞は事前チェック不要の委任によりアスタロト側で執筆。

- **仕様の裏取り（UKADOC 一次情報＋他ゴースト実物、2026-11-05）**：
  - 右クリックメニュー（オーナードローメニュー）はベースウェア描画で、ゴースト側から項目そのものの追加・差し替えはできない。変えられるのは各項目の表示名・表示可否（SHIORI リソース `*.caption`／`*.visible`）と「おすすめ」の中身だけ。追記15 でメニュー自作を見送ったのはこの制約のため。
  - `sakura.recommendsites` の URL 欄に `script:` で始まる記述を書くと、選択時にそのスクリプトが実行される（`\![raise]` も可能と UKADOC「SHIORI Resource」に明記）。→ **標準メニューを一切置き換えず、「おすすめ」配下に追加する方式**を採用。標準の導線（ゴースト情報・シェル／バルーン変更・設定・終了・標準のネットワーク更新）は全部無傷で残る。
  - 実物照合：S the Skeleton の s_string.dic（リソースは `On_<リソース名>` 関数で返す）／s_menu.dic（バルーン選択肢メニュー。ただし S の起点はダブルクリックで、本件では使わない）／s_anchor.dic（`\q[表示名,Onイベント,引数...]` でイベントが直接発火し引数が Reference に入る配線）。
  - 左ダブルクリックへの割り当てはしない（ユーザーの判断：つつき反応と競合するため）。起点は右クリック経路のみ。
  - 同梱のあやりりす（aya_lilith）は AYL_ 接頭辞の実装しか持たず、素の `On_sakura.recommendsites` は未定義のため競合しない（OnSystemLoad の上書き警告リストはりりす前提ゴースト向けの注意書き）。
  - トーク間隔の実体は yaya_base の `aitalkinterval`（秒）。SHIORI3FW.ControlAITalk が毎秒参照し、`> 0` のときだけ経過時間で発火、**0 で発話自体が停止**する。読み込み時の初期化は「変数が無い場合だけ既定値」で、保存済みの 0 を上書きしない。
- **新規辞書 astaroth_menu.dic**（_loading_order.txt に正書式で登録、関数17個）：
  - リソース：`On_sakura.recommendbuttoncaption`／`On_recommendrootbutton.caption`／`On_kero.recommendbuttoncaption`＝「アスタロトのメニュー」。`On_sakura.recommendsites`／`On_kero.recommendsites`＝項目5件（下記）。書式は項目名 (0x01) URL (0x01) バナー (0x01) 選択時スクリプト (0x02) の繰り返しで、バイト値は実績のある C_BYTE1 と CHR(2) で組み立て（aya_lilith の LinkMenuConvert と同じ並び）。script: の中身は raise で各バルーン選択肢メニューを開き、ネットワーク更新だけ `script:\![updatebymyself]`（標準の更新ボタンと同一動作。結果報告は既存の OnUpdateComplete／OnUpdateFailure が担う）。
  - **看板の立て替え**（OnAstarothSignboardMenu）：26 入浴中／27 外出中／28 勉強中／29 就寝中／30 お留守番中／しまう の選択肢は、全て既存フック `OnAstarothSignboard` を直接選択先にし、状態管理は看板辞書に一元化したまま（二重管理なし）。開いた時点の看板を導入文で表示。
  - **姿勢**（OnAstarothPoseMenu／OnAstarothPoseSelect）：立ち（0／10）／座り（20／21）／アスタロト 本を抱える8・手を重ねる6・腕組み9／フルフル 身を乗り出す16・両手を広げる17・お願い19。各選択に短い一言つき。永続状態は持たない（次のトークで通常のサーフェス選出に戻る）。
  - **トーク頻度**（OnAstarothTalkFreqMenu／OnAstarothTalkFreqSet／TalkFreqApply／TalkFreqLabel）：よく喋る180秒（約3分）／普通420秒（約7分）／静か900秒（約15分）／黙る0。選択は専用変数 `astaroth_talkfreq` に保存（YAYA グローバル変数の永続化＝看板状態と同じ仕組みで再起動後も保持）され、即時に aitalkinterval へも反映。範囲外の値は却下。変更時の確認台詞あり（設定ごと＋フルフルの一言）。「黙る」はランダムトークのみ停止し、時報・呼ばれたときの返事は対象外。
  - **ゴースト情報**（OnAstarothAbout）：版数 2.17 と内容の要約を表示。
  - 看板表示中の配慮：姿勢の選択は看板を優先して断り（看板サーフェスのまま）、頻度変更の確認とゴースト情報は看板越しの一言に切り替えて相方や通常姿を出さない。
  - テスト用フック OnAstarothMenuTest（sites／caption でリソース値の組み立て結果を返す）。
- **既存辞書の変更**：起動のたび `aitalkinterval = 420` 固定だった3箇所（astaroth_bootend.dic の OnFirstBoot／OnBoot、astaroth_otherghost.dic の OnGhostCalled）を `_r = TalkFreqApply`（保存済み設定の反映、無ければ 420）に置換。astaroth_talk.dic のヘッダ注記も現行仕様に更新（注記のみ）。
- **規律**：呼び出し結果は全て代入文で受け、裸の呼び出し文なし。波括弧は menu 53/53・bootend 6/6・otherghost 66/66・talk 33/33。新規関数17個は全辞書で重複なし。
- **検証（合成テスト、WSL の ~/sstp_menutest.py、31項目すべて合格）**：リソース値が 200 で返り、区切りバイトが正確（0x02×5件、0x01×15）／ボタン表示名／看板・姿勢・頻度の各メニューが項目つきで返る／頻度の変更（180→900→0）が確認台詞とメニューの現在表示に反映され、範囲外 123 は却下／座り選択で \s[20]・\s[21]／看板28表示中は姿勢が看板サーフェスのまま拒否され、頻度変更とゴースト情報も看板越し版になる／看板メニューが現在の看板名を表示／テスト後は看板解除・頻度 420 へ復帰、talktest=200（他辞書への影響なし）。204 等の異常はなし。
- **配信**：辞書5ファイル（astaroth_menu.dic 新規＋_loading_order.txt＋astaroth_bootend.dic＋astaroth_otherghost.dic＋astaroth_talk.dic 注記のみ）を配信フォルダへコピー（MD5 一致）、updates2.dau 再生成（140レコード）、更新フックで SSP が5ファイル全てを取得したことをログで確認（2026-11-05 19:38）。
- **nar**：v2.17 として再ビルド（`zip -D`、140エントリ＝v2.16 の139＋新辞書1）。`astaroth.nar` 差し替え＋ `astaroth_v2.17_backup.nar` 保存。
- **git**：コミット 556d840＋タグ v2.17 を push 済み。
- **実機確認（後日、ユーザー側）**：右クリック→「アスタロトのメニュー」から各バルーンメニューが開くこと、頻度変更の体感（特に「黙る」でランダムトークが止まること）。おすすめボタンの表示名が SSP の表示箇所によっては標準名のまま出る場合がある（リソース名の世代差）。その場合は実機の表示を見て調整する。
- **残作業**：readme.txt は v2 時点の記述のまま（版数・内容が古い）。今回のスコープ外として残置。次に readme を触る機会に v2.17 の内容へ更新する。

## 追記20: メニューが本体側で出ない不具合への対応（2026-11-05、nar v2.18）

ユーザーの実機報告（2026-11-05 19:49）：「おすすめ」配下の「アスタロトのメニュー」が相方（フルフル）側の右クリックでしか出ず、本体（アスタロト）側では出ない。メニューから看板を立てると相方が消え、残った側ではメニューを開けないため看板を戻せなくなる「詰み」が発生した（応急処置として SSTP スクリプトで解除済み）。

- **診断**：
  - 辞書側は対称であることを再確認した。`On_sakura.recommendsites`／`On_kero.recommendsites` は共に同じ `MenuRecommendSites` を返し、キャプションも sakura／kero／recommendroot の3つが定義されている。descript.txt にもおすすめ表示を妨げる設定はない。
  - UKADOC「SHIORI Resource」一覧（英訳版・日本語版の両方）を再確認した：`sakura.recommendsites`／`sakura.recommendbuttoncaption` はいずれも SSP 対応で、本体側にだけ付く条件や追加の要否は仕様上存在しない。→ 仕様の範囲では両側とも成立するはずで、原因はこの SSP 個体側の要求・表示挙動にあると判断した（ただし辞書側からは SSP が実際に要求した ID を直接観測できない）。
  - v2.17 の合成テストの限界も確認した：テストはテスト用フック経由で組み立て関数を直接呼んでおり、「SSP が実際に使うリソース ID で要求が来るか」は検証できていなかった。今回、その観測手段として実測カウンタを辞書に組み込んだ（後述）。
- **修正（astaroth_menu.dic v2）**：
  - **本体内側の扉を複線化**：本体側専用の別経路「ポータル」にも同じ項目一覧を載せた（`On_sakura.portalsites`＋`On_sakura.portalbuttoncaption`＋`On_portalrootbutton.caption`。ポータルも仕様上 `script:` が実行可能で、S the Skeleton やあやりりすが本体側で使う実績のある経路）。本体側では右クリック→「おすすめ」か「ポータル」のどちらかから開ける。
  - **世代差の保険**：`On_char0.recommendsites`／`On_char1.recommendsites`／`On_char0・char1.recommendbuttoncaption`／`On_sakura・kero.recommendsites.caption` にも同じ値を返すよう追加した（未使用でも無害）。
  - **実測カウンタ**：各リソース関数に要求回数のカウンタ（`astaroth_dbg_*`、永続変数）を入れ、`OnAstarothMenuTest` に `trace`（バルーン表示）／`traceclear`（消去）を追加した。実機で両者を右クリックした後に trace を読めば、SSP が実際に要求した ID が判別できる。納品時はカウンタを全て0に戻してある。
  - OnAstarothAbout の版数を 2.18 に更新し、案内文も「おすすめ／ポータル」両対応の文面にした。
- **詰み対策（astaroth_touch.dic）**：看板表示中はタッチ反応を全停止していたが、本体側（看板サーフェス）の左ダブルクリックだけを非常口として割り当て、看板をしまう（`SignboardClear` を代入文で呼ぶ）ようにした。看板表示中はつつき自体が停止しているため通常時のダブルクリック＝つつきとは競合しない。右ボタン・相方側のダブルクリックでは解除されないことも検証済み。これにより、メニューの成否に依らず、画面に残っている側から必ず看板を解除できる。
- **検証（合成テスト、WSL の ~/sstp_menutest_v218.py、25項目すべて合格）**：追加した各リソース関数（portalsites／portalbuttoncaption／char0・char1 recommendsites／portalrootbutton.caption）が辞書名どおりの呼び出しで正しい値を返すこと／カウンタが呼び出しごとに増えること／看板28表示中に右ボタン・相方側ダブルクリックでは解除されず、本体側左ダブルクリックで復帰トークつきで解除されること／解除後につつきが復活すること／talktest=200。
- **回帰テスト**：v2.17 スイート（sstp_menutest.py）と v2.16 スイート（sstp_touchtest.py）を再実行。当初 menutest の about 2件（期待文字列に残っていた「2.17」）と touchtest の看板中つつき抑制1件＋そのカスケード1件が FAIL したが、いずれも v2.18 の意図した変更（版数と非常口）にテスト側の期待値が追随していなかったもので、製品側の不具合ではないことを確認した。テスト側を v2.18 の期待値に更新し、再実行で menutest 全合格・touchtest 26項目全合格。
- **配信**：辞書2ファイル（astaroth_menu.dic／astaroth_touch.dic）を配信フォルダへコピー（MD5 一致）、updates2.dau 再生成（140レコード）、更新フックで配信し、SSP が2ファイルを 19:56 に取得したことをサーバーログで確認。作業後の状態は「看板なし・トーク頻度420（普通）・実測カウンタ全0」に戻してある。
- **nar**：v2.18 として再ビルド（`zip -D`、140エントリ）。`astaroth.nar` 差し替え＋ `astaroth_v2.18_backup.nar` 保存。zip 読み戻し検証済み（testzip 正常、変更2ファイルの MD5 がビルドツリーと一致）。
- **git**：コミット 1793b01＋タグ v2.18 を push 済み。
- **実機確認（後日、ユーザー側）**：(1) アスタロト（本体）を右クリックし、「おすすめ」と「ポータル」のどちらに「アスタロトのメニュー」が出るか。(2) フルフルも右クリックした後なら、実測 trace（SSTP で OnAstarothMenuTest に trace を送る）で SSP が実際に要求したリソース ID が判別できる。(3) 看板表示中に看板をダブルクリックして解除できること。
- **教訓**：合成テストは「自分の辞書に書いた関数名」を呼ぶだけでは不十分で、ベースウェアが実際に使う ID・経路で検証できる観測手段（今回は要求カウンタ）を最初から埋め込むべきだった。

## 追記21: 本体側メニューのグレーアウト対策と看板30の概念修正（2026-11-05、nar v2.19）

ユーザーの実機報告（2026-11-05 20:04）：(1) アスタロト（本体）側の右クリックに「アスタロトのメニュー」が2つ表示されるが、両方ともグレーアウトしてクリックできない（相方側は従来どおり開ける）。(2) 看板30（お留守番）の意味がよく分からない。あわせて親エージェント側の確認で、看板30の実装自体が概念と食い違っていることも判明した。

- **グレーアウトの切り分け（実測データに基づく）**：
  - 実測カウンタ（v2.18 で埋め込み、納品後の実機操作分）：項目＝本体おすすめ3回／相方おすすめ5回／本体ポータル3回／char0・char1は0回。名称＝本体おすすめ4回／相方おすすめ5回／本体ポータル3回／ルート系は0回。→ SSP は `sakura.recommendsites`／`sakura.portalsites` と各キャプションを実際に要求し、辞書も値を返している。それでも本体側のボタン2つだけが無効表示になる。
  - 辞書側の対称性・書式は相方側で実証済み（同じ組み立て関数の値が相方では正常動作し、書式もあやりりす LinkMenuConvert と同一の並び）。descript.txt にも妨げる設定はない。UKADOC（英日両版）にも本体側だけに付く条件は存在しない。
  - 残る差異は URL 欄の `script:` 記述のみ。対照観察として、本体側のおすすめ／ポータルで実績のある実装（S the Skeleton の s_string.dic／あやりりす前提ゴースト）はどちらも通常の http URL しか使っていない。→ **本体側のオーナードローメニュー経路では `script:` を URL として受理せず、全項目が無効化されてボタンごとグレーアウトになる**、というのが実測と最も整合する説明と判断した（SSP 内部の検証仕様そのものは非公開のため、最終確定は次回の実機クリックで、後述の二方式の成否として観測する）。
- **修正（astaroth_menu.dic v3）**：本体側の2経路を、script: を使わない別々の実績形式に振り分けた（相方側は動作実績のある script: 形式のまま不変。char0／char1 も不変）。
  - **おすすめ（sakura.recommendsites）＝第4フィールド方式**（MenuSakuraRecommendSites）：URL 欄には homeurl（http://localhost:8189/astaroth/）をダミーで置き、実行スクリプトは正規の第4フィールド（選択時スクリプト）へ移した。
  - **ポータル（sakura.portalsites）＝選択イベント方式**（MenuSakuraPortalSites＋OnRecommendsiteChoice）：URL 欄に識別子つき homeurl（?m=sign／pose／freq／update／about）を置き、選択は `OnRecommendsiteChoice`（Reference3='portal'／4=スコープ／5=位置。UKADOC のイベント仕様で確認）で受けて対応するバルーンメニューを開く（あやりりす方式）。対象は本体ポータルのみで、本体おすすめの実行に伴う通知や相方側の選択には空を返して干渉しない（二重発火防止）。ポータルのボタン名は判別用に「アスタロトのメニュー（ポータル）」へ変更（ルート側キャプションも同値）。
  - 実測カウンタに選択イベント（choice）を追加し、trace で読めるようにした。どちらの経路が実機で有効化され、選択が届いたかは、次回の実機操作後にカウンタで判別できる。
- **看板30の概念修正（astaroth_signboard.dic v2）**：「フルフルが残って留守番する」概念に表示を揃えた。
  - 立て替え（SignboardSet 30）：末尾の `\1\s[-1]`（相方を消す）をやめ、`\1\s[17]` でフルフルを画面に残す（本体＝看板30、相方＝両手を広げた立ち絵17）。
  - 再適用（OnSurfaceRestore）：30 のときだけ `\0\s[30]\1\s[17]` の2サーフェスで再適用する分岐を追加（26〜29 は従来どおり相方非表示）。
  - 呟き（SignboardMutter30）：アスタロトの語り2本（「フルフルは雷雲でお昼寝中」等）を廃し、画面にいるフルフル本人の台詞2本に書き換えた（「お留守番はバッチリだよー！」「まだかなぁ、まだかなぁ……」）。
  - 復帰トーク（SignboardReturnTalk 30）：アスタロトの台詞を「……ええ、いい子で待てていたみたいね。ご苦労さま、フルフル。」に改め、留守番していた表示と矛盾しない言い回しに揃えた。
  - なお、つつき・撫での看板中停止は30でも現行どおり停止のまま（今回は触っていない。フルフルが画面にいても看板中はタッチ反応しない）。
- **看板30の表示名の明確化**：メニュー辞書の MenuSignboardName（30）と看板メニューの選択肢ラベルを「外出中（フルフルが留守番）」に改めた（看板画像そのものの文字は今回変更していない）。
- **検証（合成テスト、WSL の ~/sstp_menutest_v219.py、46項目すべて合格）**：本体おすすめの新書式（5項目／script: を含まない／ダミーURL／第4フィールドに raise と updatebymyself）／本体ポータルの新書式（5項目／?m= 識別子×5／スクリプトを含まない）／相方おすすめが従来書式のまま／ポータルキャプションの判別名／OnRecommendsiteChoice の項目対応（0=看板メニュー＝新ラベルつき／1=姿勢／2=頻度／3=updatebymyself そのもの／4=情報2.19）とガード（recommend・相方・範囲外は無応答）／選択イベントカウンタが呼び出し回数どおり8／看板30の立て替え・再適用に `\1\s[-1]` が含まれず `\1\s[17]` で相方が残ること／30 の呟きがフルフル本人の台詞2本とも出ること（語り文は出ない）／30 でも非常口（本体ダブルクリック）で復帰トークつき解除できること／28 は従来どおり相方を消すこと（回帰）。
- **回帰テスト**：v2.17 スイート（sstp_menutest.py。期待値の版数 2.18→2.19 の2件は意図した変更として追随）と v2.18 スイート（sstp_menutest_v218.py。portalsites の期待値を新書式の ?m=sign に追随）を再実行し全合格。タッチスイート（sstp_touchtest.py）も26項目全合格、talktest=200。異常（204等）はなし。テスト後は看板なし・頻度420・実測カウンタ全0（選択イベント含む）に戻してある。
- **配信**：辞書2ファイル（astaroth_menu.dic／astaroth_signboard.dic）を配信フォルダへコピー（MD5 一致）、updates2.dau 再生成（140レコード）、更新フックで配信し、SSP が2ファイルを 20:12 に取得したことをサーバーログで確認。
- **nar**：v2.19 として再ビルド（`zip -D`、140エントリ）。`astaroth.nar` 差し替え＋ `astaroth_v2.19_backup.nar` 保存。zip 読み戻し検証済み（testzip 正常、変更2ファイルの MD5 がビルドツリーと一致）。
- **git**：コミット 37d7552＋タグ v2.19 を push 済み（本追記の記録コミットとともに行う）。
- **実機確認（次回、ユーザー側）**：(1) アスタロトを右クリックし、「アスタロトのメニュー」（おすすめ）と「アスタロトのメニュー（ポータル）」のどちらが（あるいは両方が）クリックできるようになったか。(2) 開けた方で項目を選ぶとバルーンメニューが開くか。ポータル側は仕組み上、選択時にブラウザで localhost のページが開く場合がある（無害だが、その場合は方式の採否を再検討する）。(3) 両者を試した後なら trace で選択イベントの回数が読め、どちらの方式が届いたか最終確定できる。(4) 看板30を立てて、フルフルが画面に残ること・呟きがフルフルの台詞になること。

## 追記22: 看板30でのフルフル反応追加と、本体側メニューのリンク置き場化（2026-11-05、nar v2.20）

ユーザーの実機確認（2026-11-05 20:18）を受けた対応。当初の指示は「(1) 本体側メニュー：対照実験→ペンダント等の当たり判定に専用部位を足す代替扉を実装」「(2) 看板30の間、フルフルへのクリック反応を追加」の2件だったが、作業中にユーザーの判断が変わり、(1) は大幅に縮小された。

- **件1（本体側メニュー）は方向転換のうえ縮小**：
  - ユーザーの判断：「看板状態をクリックで解除できるなら、フルフル側だけにメニューがあっても問題はない」。→ **代替扉（Menu 部位の追加、surfaces.txt の collision 編集）は実装しない**ことになった。着手は実画像の寸法測定（surface0 のペンダントは x215〜272／y300〜352 付近に金色の装飾が集中）までで、ファイル変更には至っておらず、取り消しも不要だった。対照実験（通常 https URL だけのエントリで有効化を切り分ける）も製品としては不要となり、未実施のまま取りやめた。
  - **本体側のおすすめ／ポータルがグレーアウトのままである点は、ユーザーが現状で了承**したものとして記録する（扉は相方側メニュー＋看板のダブルクリック解除で足りる、という判断）。v2.19 までに入れた本体側の2方式（第4フィールド／選択イベント）の組み立て関数は、害がないため未使用のまま残置した。
  - 代わりに、ユーザー提案で**本体側の2経路を「リンク置き場」に転用**した：`sakura.recommendsites` と `sakura.portalsites` の中身を、通常 URL のリンクエントリ「Muse」→ https://muse.ai の1件（通常の recommendsites 書式、選択時スクリプトは空）に置き換えた（組み立ては新設の `MenuSakuraLinkSites`）。本体側のキャプション（sakura.recommendbuttoncaption／sakura.portalbuttoncaption／recommendrootbutton.caption／portalrootbutton.caption／sakura.recommendsites.caption の保険形式）は中身に合わせて「リンク」に改めた。相方側のキャプションとメニュー（script: 形式）は従来どおり不変。char0／char1 の保険経路は要求実績0のため不変。
  - `OnRecommendsiteChoice` の扱い：本体ポータル分は不要になったが、削除せず**応答条件を絞って残置**した。Reference1 に '?m=' を含む場合（旧方式の識別子つき URL）だけ応答し、通常リンクのクリックでは空を返す（二重発火防止のガードは維持）。通常リンクのクリックでバルーンメニューが誤発火しないことは合成テストで確認済み。
  - **有効化の最終判定は実機でしかできないため、ユーザーの次回右クリックで「リンク」ボタンが有効化されているかを確認してもらう**。グレーアウトのままなら現状と同じで損失はない、という位置づけ。
- **件2（看板30でのフルフル反応）を実装（astaroth_touch.dic）**：
  - ゲート追加：看板番号を返す `TouchSignNumber` を新設。OnMouseDoubleClick は、看板30の間に限りスコープ1（フルフル）の左ダブルクリックを `TouchPoke` へ通す（クールダウンは対象別5秒の既存仕組みを共用）。OnMouseMove は、看板30の間に限りスコープ1の Head 往復を撫でとして追跡する（クールダウン20秒・段階の累積も既存仕組みを共用）。
  - 専用プール：看板30中は本体側が看板サーフェスを表示しているため、通常プールの相方掛け合い（`\0` の台詞・`\0\s[..]` の表情変更）を混ぜると看板表示が切り替わって崩れる。そこでフルフル単独の台詞だけの専用プールを用意した。つつきは `TouchPokeTalkF30` 経由の4種（頭3本／顔2本／胸2本／その他2本。通常プールの彼女の台詞を基に掛け合いを外し、「お留守番中に驚かせるなんてー」「お留守番中でも、だめなものはだめ」等の留守番の味付けを加えた）。撫では段階別の3プール（`TouchNadeF30_1〜3`、各2本。「お留守番のご褒美」等）。
  - 維持したもの：アスタロト側（看板）への反応は停止のまま、非常口（本体側ダブルクリックで看板をしまう）は看板30でも従来どおり動作。26〜29 は全面停止のまま（看板28で相方のつつき・撫でが無反応であることをテストで確認）。
- **OnAstarothAbout の更新**：版数を 2.20 にし、案内文を実態に合わせた（「フルフルを右クリックして『アスタロトのメニュー』を開きなさい。私の側のボタンは、リンク置き場になっているわ」）。
- **検証（合成テスト）**：新規スイート（WSL の ~/sstp_test_v220.py、49項目すべて合格）：本体おすすめ／ポータルがリンク書式の値を返すこと（1件・Muse・https://muse.ai・script: なし）／本体キャプションが「リンク」／相方側メニューが従来どおり（5件・script: 形式・キャプション不変）／OnRecommendsiteChoice が通常リンクで無応答・?m= 付きでは看板メニューを開く・ガード（recommend／相方）維持／看板30でフルフルのつつき（部位4種・クールダウン・右ボタン無反応）と撫で（段階1〜3）が専用プールで発火し、台詞に `\0\s[` を含まないこと／看板30で本体側の撫でが無反応・非常口で解除できること／看板28では全面停止のまま・非常口動作／talktest=200。
- **回帰テスト**：タッチスイート（sstp_touchtest.py、26項目）は無変更で全合格。メニュー系3スイート（sstp_menutest.py／v218／v219）は、本体側の書式・キャプション・版数の期待値だけを v2.20 の意図した変更に追随させて全合格（製品側の不具合による FAIL はなし）。
- **配信**：辞書2ファイル（astaroth_touch.dic／astaroth_menu.dic）を配信フォルダへコピー（MD5 一致）、updates2.dau 再生成（140レコード）、更新フックで配信し、SSP が2ファイルを 20:26 に取得したことをサーバーログで確認。作業後の状態は「看板なし・トーク頻度420（普通）・実測カウンタ全0・タッチ状態初期化」に戻してある。
- **nar**：v2.20 として再ビルド（`zip -D`、140エントリ＝v2.19 と同一集合、変更は辞書2ファイルのみ）。`astaroth.nar` 差し替え＋ `astaroth_v2.20_backup.nar` 保存（いずれも 22,601,776 bytes）。zip 読み戻し検証済み（testzip 正常、変更2ファイルの MD5 がビルドツリーと一致）。
- **git**：コミット 7ac0624＋タグ v2.20 を push 済み（本追記の記録コミットとともに行う）。
- **作業中の事故と復旧**：編集後、転送の過程でローカルの astaroth_menu.dic が astaroth_touch.dic の内容に化けている事象を MD5 照合で検出した。SSP 実機へは未配信の段階だったため実害はなく、menu.dic は git（v2.19）から復元し、編集は一致回数を検証するスクリプトで再適用した（再適用後の MD5 は事故前に記録した値と一致）。以後の転送は1ファイルずつ行い、前後で必ず MD5 を照合した。
- **実機確認（次回、ユーザー側）**：(1) アスタロトを右クリックし、「リンク」ボタン（おすすめ／ポータル）が有効化されているか。押せれば Muse（https://muse.ai）が開くはず。(2) 看板30（外出中・フルフルが留守番）を立てて、フルフルをつつく・頭を撫でる反応が出ること。

## 追記23: 本体おすすめへの本物のメニュー復帰（2026-11-05、nar v2.21）

ユーザーの実機確認（2026-11-05 20:51）で、メニュー問題の様相を変える事実が判明したを受けた対応。

- **判明した事実**：本体側の「リンク」ボタン2つ（おすすめ／ポータル）は、当初グレーアウトしていたが **ゴーストを再起動したら有効になった**。一方、相方側のメニューは v2.17 配信直後（再起動なし）でも使えていた。看板30でのフルフルのつつき反応も有効だった（確認済み）。
- **示唆される挙動**：本体側のおすすめ／ポータルは、**起動時に読んだ状態で固定され、ネットワーク更新による辞書のリロードでは有効状態が更新されない**らしい。つまり v2.17〜v2.19 のグレーアウトは、書式（script: の可否や第4フィールド方式など）が原因ではなかった可能性が高い。v2.19 で立てた「本体側経路は script: を受理しない」という説明は、この新事実の前では根拠を失ったものとして扱う（当時の実測＝要求回数と返値の正常さとは矛盾しない）。
- **変更（astaroth_menu.dic v5、変更はこの1ファイルのみ）**：
  - `sakura.recommendsites` を、相方側で動作実績のある script: 形式の5項目（`MenuRecommendSites` と同一内容）に戻した。
  - 本体おすすめのキャプションを「アスタロトのメニュー」に戻した（`sakura.recommendbuttoncaption`／`recommendrootbutton.caption`／保険形式 `sakura.recommendsites.caption` の3箇所）。
  - **本体ポータルはリンク置き場のまま維持**：`sakura.portalsites` は `MenuSakuraLinkSites`（Muse→https://muse.ai の1件）、ポータル側キャプションは「リンク」のまま。相方側は一切変更なし。`OnRecommendsiteChoice` の絞り込み（Reference1 に '?m=' を含むときだけ応答）も維持。
  - `OnAstarothAbout` の版数を 2.21 にし、案内文を実態に合わせた（「私かフルフルを右クリックして、おすすめの『アスタロトのメニュー』を開きなさい。ポータルの方は、リンク置き場になっているわ」）。
  - v2.19 の旧方式の組み立て関数（MenuSakuraRecommendSites／MenuSakuraPortalSites）は従来どおり未使用のまま残置。
- **検証（合成テスト）**：新規スイート（WSL の ~/sstp_test_v221.py、48項目すべて合格）：本体おすすめが5項目・script: 形式で相方側とバイト単位で同一の値を返すこと／本体おすすめのキャプションが「アスタロトのメニュー」／本体ポータルがリンク1件（Muse・https://muse.ai・script: なし）でキャプション「リンク」のまま／OnRecommendsiteChoice の絞り込みとガード維持／About 2.21 と案内文／看板30でフルフルのつつき・撫でが専用プールで発火し本体側は無反応・非常口で解除できること／看板28では全面停止のまま／看板・頻度のバルーンメニューが開くこと／talktest=200。作業後の状態は「看板なし・トーク頻度420（普通）・実測カウンタ全0・タッチ状態初期化」に戻してある。なお合成テストで確認できるのは返値までであり、**本体おすすめの有効化そのものはユーザーの再起動後にしか実機で確定できない**。
- **配信**：辞書1ファイル（astaroth_menu.dic）を配信フォルダへコピー（MD5 0f6edadb195374c67b79fd8244bad54b で一致）、updates2.dau 再生成（140レコード）、更新フックで配信し、SSP が astaroth_menu.dic を 20:54:58 に取得したことをサーバーログで確認。
- **nar**：v2.21 として再ビルド（`zip -D`、140エントリ＝v2.20 と同一集合、内容差分は astaroth_menu.dic のみ・MD5 一致）。`astaroth.nar` 差し替え＋ `astaroth_v2.21_backup.nar` 保存（いずれも 22,602,274 bytes）。zip 読み戻し検証済み（testzip 正常）。
- **git**：コミット ff9f6a2＋タグ v2.21 を push 済み（本追記の記録コミットとともに行う）。
- **教訓（v2.17〜v2.20 のグレーアウト騒動の総括）**：**SSP 本体側のおすすめ／ポータルは起動時読み込みで固定されるらしく、メニュー系リソースの変更はゴースト再起動後に実機確認すること。** 配信直後の実機表示だけで書式の成否を判断しない。合成テストは「辞書が返す値」までしか保証せず、SSP 側の有効状態は再起動を挟まないと観測できない、という前提で確認手順を組むこと。
- **実機確認（次回、ユーザー側）**：ゴーストを再起動したうえで、(1) アスタロトを右クリックし、おすすめ「アスタロトのメニュー」が有効化されていて、5項目からバルーンメニューが開くこと。(2) ポータル「リンク」が引き続き有効で、Muse（https://muse.ai）が開くこと。

## 追記24: 第2シェル（夜セット）の候補イラスト生成（2026-11-05、候補作りのみ・未実装）

- **背景**：シェル切り替えの議論から「夜はネグリジェに着替える第2シェル」案が出た。順番は入浴後（23時の入浴看板以降〜翌7:30）が優先で、夜中に看板をどけて呼び出されたときもネグリジェ姿、というユーザーの設計。今回はシェル組み立て・辞書には手を付けず、採用候補の生成とユーザーの選択用プレビューまで。
- **生成**：`work/gen_night_candidates.py`（WSL 実行）。既存ブループリント（CottonAnima base1、832×1216、30step/CFG4/er_sde、緑背景・全身立ち姿）を踏襲し、衣装だけを差し替えた。全10点が生成成功（21:14〜21:19）。
  - アスタロト ネグリジェ 4点（A1 seed20261111 膝丈／A2 seed111101／A3 seed777101 短め丈／A4 seed424201 薄手の黒レースガウン羽織り案）。固定タグセット（紫黒の長髪・琥珀の目・金のペンダント・光輪）は維持し、衣装は黒〜深紫シルク＋レース縁取りのネグリジェに変更。いずれも半眼で眠そうな表情に寄った。
  - フルフル パジャマ 3点（P1 seed20261112／P2 seed111201／P3 seed777201）。ピンクのフリル付きパジャマ上下＋スリッパ、白翼・青い宝石目・頬の赤みは仕様通り。
  - フルフル 短いネグリジェ 3点（N1 seed20261113／N2 seed111301／N3 seed777301）。膝上のピンク〜白ベビードール＋白レース。
- **検品**：全10点を目視し、顔・手の大きな破綻や衣装の取り違えは無し（振り直し不要）。制作時の注意点として、A4 はガウン裾が床まで引きずる形（キーイング時に裾処理の検討が必要）、P1 は髪が低めの緩いツインテール寄りで他2点よりツインテール感が弱い、P3／N3 は足元に濃い影ブロック、複数点に頭周りのキラキラ等の浮遊物（既存工程で除去可能な範囲）。
- **成果物**：候補ファイルと選択用プレビュー（統合1枚＋グループ別3枚、全て番号ラベル付き）を `work/night_candidates/` に配置。プロンプトとシードの対応は `work/night_candidates/prompts.md` に集約（採用後の量産で再現可能）。
- **次工程（未着手）**：ユーザーが A 群から1点、フルフルは P 群／N 群のどちらか系統＋1点を選んだら、表情差分の量産・キーイング・第2シェル組み立て・夜シェルへの自動/手動切り替え辞書へ進む。

## 追記25: 第2シェル（夜セット）候補イラスト第2便・色替え（2026-11-05、候補作りのみ・未実装）

- **背景**：第1便（追記24）へのユーザーの評は「どれも可愛いが通常版と似すぎている。特にフルフルのネグリジェは普段着（ピンクのフリルドレス）とよく似ている。他の色も見せて」。色で明確に差をつけることを目的に第2便を生成した。
- **生成**：`work/gen_night_candidates2.py`（WSL 実行）。条件は第1便と同一（CottonAnima base1、832×1216、30step/CFG4/er_sde、緑背景・全身立ち姿）。全10点が生成成功。番号は第1便からの続き。
  - アスタロト ネグリジェ別色 4点（A5 seed20261211 アイボリー白・膝丈／A6 seed121201 ワインレッド・膝上／A7 seed777401 淡ラベンダーブルー・ロング丈＋シアーなガウン羽織り／A8 seed424501 エメラルドグリーン・膝丈）。髪・瞳・金のペンダント・光輪は維持。
  - フルフル パジャマ別色 3点（P4 seed20261212 水色・星と三日月柄／P5 seed121501 ミントグリーン・星柄／P6 seed777501 ラベンダー・三日月柄）。ピンクを外し、夜モチーフの柄で差をつけた。
  - フルフル 短いネグリジェ別色 3点（N4 seed20261213 白＋ピンクのリボン／N5 seed121601 黒＋白レース／N6 seed777601 水色＋白レース）。ピンクを外し、普段着と並べて別物に見えることを優先した。
- **検品**：全10点を目視し、顔・手の大きな破綻や衣装の取り違えは無し（振り直し不要）。注意点として、A7 は A4 と同様ガウン裾が床に広がる形（キーイング時に裾処理の検討が必要）、P4 は髪の一部に透かし状の微かな文字様の乱れ（拡大時のみ視認できる程度）、P5 はツインテールが短く他2点よりツインテール感が弱い、P6 は頭周りにキラキラ浮遊物（キーイングで除去可）。
- **成果物**：候補10点を `work/night_candidates/` に追加し、第2便のみのコラージュ `preview_round2.png`（番号ラベル付き）を作成（生成: `work/make_night_preview2.py`）。プロンプトとシードの対応は `work/night_candidates/prompts.md` に追記した。
- **次工程（未着手）**：第1便・第2便を通してユーザーが各群から採用点を選んだら、表情差分の量産・キーイング・第2シェル組み立て・夜シェルへの自動/手動切り替え辞書へ進む。

## 追記26: 第2シェル「night」（夜セット）の実装と時刻連動の自動切り替え（2026-11-05、nar v2.22）

追記24・25 の候補からユーザーが採用を決定：アスタロト＝**A7**（淡いラベンダーブルーのロングネグリジェ＋シアーガウン、seed 777401）、フルフル＝**N5**（黒の短いネグリジェ＋白レース、seed 121601）。パジャマ案（P群）は不採用。

- **絵の量産**（`work/gen_night_expr.py`、WSL ComfyUI、候補と同条件）：土台と同シード・同衣装指定で表情指定だけを差し替える既存ワークフロー（gen_expr.py／gen_furfur_expr.py）で、アスタロト surface1〜5、フルフル surface11〜15 を生成。全10点が一発で成功し振り直しなし。base の 0／10 は採用候補の生成画そのものをキーイングした。
- **キーイング**：アスタロトは finalize_expr.py（幅はガウンの広がりで 725〜743、surface6 の 630 と同種の広幅。6枚とも bbox 上端 y24〜27・下端 y1190〜1193 で相互に揃う）。フルフルは finalize_furfur.py の夜版（`work/finalize_night_furfur.py`、JOBS のファイル名だけ差し替え）で一括正規化し 833×1216・下端 1211 に統一（通常シェル 835×1216 とほぼ同寸）。pna とアルファの一致・四隅透過を検証済み。
- **シェル構築**：`shell/night/`（descript の name はフォルダ名と一致させて `night`）。全35サーフェスを master と並行番号付けし、0〜5／10〜15 を夜セットに差し替え、残り（ポーズ6〜9・46〜49・16〜19・56〜59、座り20・21、看板26〜30）は master の画像コピーを仮置き（番号欠けで表示が消える事故の防止）。surfaces.txt は master の複製を土台に、0〜5 と 10〜15 の当たり判定だけ最終画像の実測へ差し替えた（暗背景＋50pxグリッドで目視実測：アスタロト Head 215,55,505,265／Face 270,145,450,255／Bust 255,330,475,485。フルフル Head 230,45,600,330／Face 320,150,505,290／Bust 310,335,520,490）。静的確認：両シェルとも定義35＝png35＝pna35 で欠けなし。
- **自動切り替えの仕様裏取り**（UKADOC さくらスクリプト一覧／SHIORI Event 一覧）：切り替えは `\![change,shell,シェル名]`（該当シェルが無ければ無視。用例 `\![change,shell,master]`）。切り替え後は `OnShellChanged`（Reference0=現在のシェル名）が通知されるため、現在シェルを変数で追跡でき、SSP メニューからの手動切り替えにも追従できる。実機の state 表示でも現在名が「Master」と返ることを確認した。
- **辞書**（新規 `astaroth_shell.dic`、`_loading_order.txt` に正書式で追加）：夜の定義は **23:00〜翌7:30**（GETTIME による時刻判定のみ、毎秒監視なし）。「姿を現す場面」のスクリプト先頭に、目標と違うときだけ切り替えタグを前置する：OnBoot（bootend、看板の起動時吸収を含む。起動時は未記録でも目標へ寄せる force 付き）、看板解除 SignboardClear（signboard。朝7:30 の自動解除もこの経路で通常シェルへ戻る）、他ゴーストに呼ばれた OnGhostCalled の反応（otherghost、抑制時は付けない）。現在シェルの追跡は OnShellChanged→変数 `astaroth_shell_name`。テスト用フック OnAstarothShellTest（時刻上書きは時・分の別変数。除算・剰余は実績構文に無いため避けた）。
- **手動切り替え**（astaroth_menu.dic v6）：おすすめ項目に「衣装を変える」を追加（全経路6項目に）。OnAstarothShellMenu／OnAstarothShellSet でその場だけ切り替え、次に「現す場面」で時刻判定に再び合わされる。看板表示中は姿勢メニューと同様に断る。OnAstarothAbout の版数を 2.22 にし、夜の着替えの一文を追加。
- **検証**（WSL `~/sstp_shelltest.py`、新規21項目すべて合格）：境界時刻の目標判定（22:59=master／23:00=night／0:00・6:59・7:29=night／7:30=master／12:00=master）、同期タグの発火と一致時の無発火、看板解除への同梱（夜=night タグ＋復帰トーク／昼=master タグ／一致時はタグなし）、手動メニューと手動切り替え（不正値は拒否）。なお NOTIFY の応答スクリプトは SSP が実際に実行するため、テスト中に実シェルも night↔master を往復し、最終状態は「目標 master／現在 Master・看板なし・時刻上書き解除」に復帰済み。talktest=200。回帰のメニュー系2スイートは、意図した変更（項目数 5→6、About の版数 2.21→2.22）への期待値遅れのみ FAIL で、製品側の不具合なし（頻度・看板・姿勢の各フローは合格）。
- **配信**：変更78ファイル（辞書6＋shell/night 72）を配信フォルダへコピーし、updates2.dau を 213 レコードで再生成。更新フックで SSP が全78ファイルを取得したことをサーバーログで確認（22:15）。
- **nar**：v2.22 として再ビルド（`zip -D`、213エントリ＝v2.21 の140＋night 72＋astaroth_shell.dic 1、testzip 正常、v2.21 からの欠落なし、42,534,785 bytes）。`astaroth.nar` 差し替え＋ `astaroth_v2.22_backup.nar` 保存。途中経過はコミット 58c6665（辞書）／2c2c5fe（シェル）で刻んだ。
- **実機確認（未実施、ユーザーの明日の夜の確認待ち）**：(1) シェル追加が SSP に認識されるかは、ゴースト再起動後にシェル切り替えメニューへ「night」が出るかで確認（おすすめリソースの前例どおり、再起動が要る可能性が高い）。(2) 夜セットの見た目（A7 のガウン裾の広がり、髪縁に残る緑みの許容可否、当たり判定の位置）。(3) 23:00 以降に看板を下ろしたとき、ネグリジェ姿で現れるか。(4) 仮置きのポーズ・座り・看板は通常シェルと同じ絵のまま（夜セットへの差し替えは今後の課題）。

## 追記27: 夜シェルの仮置き全解消と通常フルフルの頭身是正（2026-11-06、nar v2.23）

ユーザーの指示（2026-11-05夜）に基づく2部構成。第1部・第2部とも完遂し、v2.23 として配信済み。辞書変更なし。

- **キーイング方式の刷新（両部共通）**：従来のフラッドフィル＋緑優位ランプに、(1) 四隅サンプルから求めたキー色への色距離ベースの除去（囲まれた領域にも届く。dist<55 かつ緑優位の画素は連結性によらず透明化、55〜110 は減衰）、(2) デスピル強化（G の上限を max(R,B)+8）、(3) 床影パス（暗く緑優位な画素を影として除去）を追加した新工程 `work/finalize_v223.py` を使用。全差し替え面で「不透明画素のうち緑優位度30超」の残存は 0px を数値確認。夜 surface0 の光輪内側は、市松模様への合成確認画像（work/v223_preview/night0_halo_checker.png）で透明を目視確認した（旧版は緑優位度10〜15の淡い緑みが737px残っていた）。ついでに通常シェルのアスタロト surface0 も点検した：光輪内側は既に透明で、緑残存は 0px（修正不要だった旨を報告に添える）。
- **第1部（夜シェル shell/night の仮置き差し替え）**：生成は `work/gen_v223.py`（既存ポーズ量産ワークフロー踏襲、WSL ComfyUI、832×1216、30step/CFG4/er_sde、採用土台と同シード）。
  - アスタロト A7：ポーズ 6（手を重ねる、716×1216）・7（手を合わせ俯く、430×1216）・8（本を抱える、730×1216）・9（腕組み、643×1216）と表情違い 46（笑顔）・47（目閉じ）・48（笑顔）・49（通常）。8 は足元の床影が色距離でも残ったため、足元領域に限定した追加マスクで除去した。
  - フルフル N5（頭身指示つき）：ポーズ 16（身を乗り出す）・17（両手を広げて喜ぶ）・18（拗ねてそっぽ）・19（お願い）と表情違い 56（照れ）・57（目閉じ）・58（驚き）・59（笑顔）。16／56 は前のめり姿勢でツインテールが髪の後ろに回り短髪風に見える（実害は小さいと判断し許容）。
  - 座り：20（アスタロト A7）・21（フルフル N5）。看板 26〜30 は対象外で現行のまま。
  - 基本面 0〜5・10〜15 は新規キーイングで再抜き（配置は旧面の bbox へ中心・下端を合わせて維持、当面の当たり判定は不変）。
  - 当たり判定はポーズ・座りの全20面について、旧面 bbox → 新面 bbox の線形変換で最終画像の実測に基づき付け替えた（`work/update_surfaces_v223.py`）。
  - プレビュー：work/v223_preview/night_poses_new.png で全18面を目視確認（ポーズの意味づけ・顔・夜衣装の一致を確認）。
- **第2部（通常シェル shell/master のフルフル全15面の頭身是正）**：対象は 10〜15・16〜19・56〜59・21 の全15面。デザイン（ピンクのフリルドレス、seed1031系譜の顔・髪型）は維持し、プロンプトに頭身指示（slender body, long legs, tall proportions, small head、約6頭身の文章指定、negative に chibi／super deformed／short legs／large head 等）を全ジョブへ入れた。検品基準は「現行 surface17 のバランス」と「アスタロト基本面と並べた身長感」で、比較シート（work/v223_preview/master_furfur_compare.png）で新旧を目視比較した：新10 は旧10より明確に脚が長く細身になり、新17 は基準の旧17 とほぼ同バランスに収まった。
  - 振り直し1回：初回の基本6面は翼が旧デザインより大きく垂れ下がったため、翼の指定を「two small white feather wings（肩の後ろに小ぶり）」へ直し、negative に huge/large/long wings を足して6面を再生成した（ComfyUI の連番保存で _00002_ になる点に注意）。再生成後の翼は旧デザインと同寸感に復帰。14（照れ）は伏し目＋強い頬染めの表現になったが照れとして成立すると判断し許容。
  - 配置は基本6面を一括正規化（810×1216、中心・下端1211で統一）、ポーズ・座りは単体配置。当たり判定は全15面を実測 bbox から付け替え（master 側 surfaces.txt の該当箇所のみ。アスタロト側の面と看板には触っていない）。
- **検証**：静的確認は両シェルとも定義35＝png35＝pna35・欠け番号なし。全差し替え面で pna＝アルファ完全一致・四隅 alpha=0・透明画素 RGB=(0,255,0)。合成テスト：talktest は発話成功（200相当）、shelltest は全項目 PASS（夜シェルへの手動切り替え・復帰・時刻同期を含む）。
- **配信**：変更92ファイル（night 61＋master 31）を WSL 配信フォルダへコピー（MD5 一致を確認）、updates2.dau を 213 レコードで再生成。更新フックで起動し、配信サーバーログで SSP が 10:54 に全92ファイルを取得したことを確認（GET 94件＝差分92＋照合表等）。
- **nar**：v2.23 として再ビルド（`zip -D`、213エントリ＝v2.22 と同一集合、testzip 正常、40,063,930 bytes）。`astaroth.nar` 差し替え＋ `astaroth_v2.23_backup.nar` 保存。
- **git**：コミット bd816be＋タグ v2.23 を push 済み（本追記の記録コミットとともに行う）。
- **実機確認（後日、ユーザー側）**：ゴースト再起動後に、(1) 夜間帯に看板を下ろして夜ポーズ・座りが夜衣装で出ること、(2) 通常フルフルの新旧の身長感（アスタロトと並んだときの釣り合い）、(3) 光輪内側の緑が消えていること。

## 追記28: 夜シェル フルフル基本面の頭身是正（2026-11-06、nar v2.24）

ユーザーの実機確認（2026-11-06 19:19）で残っていた1点への対応：v2.23 では夜シェル基本面 10〜15 は新規キーイングでの再処理のみで、生成自体は v2.22 時点（頭身指示なし）のままだった。今回はその6面を頭身是正つきで再生成した。辞書変更なし。通常シェルと夜のアスタロト面には触っていない。

- **生成**（`work/gen_v224.py`、WSL ComfyUI、832×1216、30step/CFG4/er_sde、土台シード121601）：gen_v223.py の furfur_master_base と同流儀で、N5（黒の短いネグリジェ＋白レース）の衣装指定に頭身指示（PROP_TAGS／PROP_PROSE／PROP_NEG：slender body, long legs, tall proportions, small head、約6頭身、negative に chibi／super deformed／short legs／large head 等）を全6面へ入れた。表情対応は 10=通常の笑顔・11=満面の笑顔・12=驚き・13=拗ね・14=照れ・恋・15=目閉じ。全6面 success（rc=0）。
- **後処理**（`work/finalize_v224.py`）：v2.23 で確立した色距離キーイング＋囲み領域除去＋デスピル強化。基本面の一括正規化（place_group、836×1216・中心統一・下端1211）で配置。全6面とも緑残り 0px・pna＝アルファ完全一致を確認。
- **検品**（プレビュー `work/v224_preview/`：night_furfur_base_new.png＝新6面一覧、night_furfur_compare.png＝旧10・旧11／新10・新11 と night17（v2.23）の比較、night_height_pair.png＝夜アスタロト0との並列）：新6面は旧面より脚が長く頭が小さく、物差しの night17 と同じバランスに収まった。夜アスタロト基本面と並べても頭頂・足元がほぼ揃い、身長感はほぼ同じに見える。顔・髪型・衣装は夜ポーズ面（16〜19・56〜59・21）と同一系統で揃っている。12（驚き）の翼はやや垂れ気味だが欠落はなく許容した。振り直しなし。
- **当たり判定**：`work/update_surfaces_v224.py` で night 側 surfaces.txt の 10〜15 のみ、旧 bbox → 新 bbox の線形変換で実測付け替え（例：surface10 の bbox は (6,826,51,1211) → (8,827,40,1211)）。
- **検証**：静的確認は両シェルとも定義35＝png35＝pna35・欠けなし。変更は night の surface10〜15（png/pna）＋ surfaces.txt の13ファイルのみ。合成テスト：talktest は発話成功（TALK PLAYED）、shelltest は ALL PASS（最終状態は目標 master／現在 Master に同期復帰）。
- **WSL接続の不安定**：19:20〜20:57 の間、muse-ssh（Tailscale経由）が「proxy closed connection」で断続的に全滅した（ComfyUI への HTTP も 000）。原因は未確定（WSL 側の停止／再起動が疑われ、配信サーバー等のプロセス開始時刻は 20:58 を示していた）。20:57 に復旧し、生成〜配信を 21:04 までに完了した。
- **配信**：変更13ファイルを WSL 配信フォルダへコピー（MD5 一致を確認）、updates2.dau を 213 レコードで再生成。更新フックで起動し、配信サーバーログで SSP が 21:04 に全13ファイル＋照合表を取得したことを確認（全て 200）。
- **nar**：v2.24 として再ビルド（`zip -D`、213エントリ＝v2.23 と同一集合、testzip 正常、39,949,384 bytes）。`astaroth.nar` 差し替え＋ `astaroth_v2.24_backup.nar` 保存。
- **git**：コミット 4787996＋タグ v2.24 を push 済み（本追記の記録コミットとともに行う）。
- **実機確認（後日、ユーザー側）**：夜間帯（23:00〜7:30）に夜シェルでフルフルの基本・表情面が新しい頭身で出ること。

## 追記29: 季節トーク（静的な季節ネタ）実装（2026-11-06、nar v2.25）

ユーザーが「動的トーク」の意味を確認したうえで「まずは静的な季節ネタを作ろう」と決め、当日作成した原稿 TALKS_SEASONAL.md（全77本・18キー）を即日承認。本追記はその実装・配信の記録。

- **辞書**（新規 `astaroth_seasonal.dic`、`_loading_order.txt` に正規書式で登録）：原稿の77本を18の季節プール（TalkSeason*、: nonoverlap）に1対1で実装。日付判定は GETTIME（[1]=月、[2]=日）で、SeasonFuncFor の if/elseif の並び順で「行事の狭い窓 → 月別基調」の優先度を表す。実効期間の要点：正月 1/1〜7／寒中 1/8〜31／節分 2/2〜4／バレンタイン 2/13〜14／桜 3/21〜31（原稿は「3月下旬〜4月上旬」だが、4月は新年度を優先し 4/1 は新年度になるよう調整）／新年度 4月／GW 4/29〜5/6／梅雨 6月／七夕 7/6〜8／酷暑 7/21〜8/31（お盆 8/13〜16 を除く）／秋口 9月／紅葉 10/1〜11/20／ハロウィン 10/30〜31／冬支度 11/21〜30／クリスマス 12/24〜25／年末 12/26〜31／冬基調 12/1〜23 と 2月の行事以外。3月前半・5/7〜31・7/9〜20 は季節なし。
- **選択への組み込み**（astaroth_talk.dic の TalkSelectOne のみ変更）：季節キーが有効な期間は先に 20％ の抽選で季節プールを引き、外れたら従来配分（時間帯25％／掛け合い45％／独白各15％）で選ぶ。季節なしの日は従来どおり。季節プールも RandomTalk の履歴回避（直近5件）の対象。音声は付けない（現行方針どおり）。
- **テスト用フック**：OnAstarothSeasonTest（shell 辞書と同型。date で日付上書き、clear で解除、key でプール名確認、draw で実引き）。送信スクリプトは WSL の ~/sstp_seasontest.py。
- **About 版数**：astaroth_menu.dic の OnAstarothAbout を 2.22 → 2.25 に（看板越し・通常の両分岐。文面は他を変更せず）。
- **検証**：静的確認として各プールの本数を原稿と照合（5,4,4,4,5,4,4,5,4,5,4,4,4,4,4,4,5,4＝計77本、過不足なし）、シェル側は無変更。合成テスト（sstp_seasontest.py）全29項目 PASS：日付境界21件（指定の 1/3 正月・2/3 節分・2/14 バレンタイン・4/1 新年度・5/20 なし・7/7 七夕・8/14 お盆・10/31 ハロウィン・12/24 クリスマス・12/31 年末・12/10 冬基調を含む）、クリスマスプールの実引き3回、季節なし日の引き出し不可、12/24 上書きでの RandomTalk 40回サンプリング（全200、季節行 6/40 ヒット＝設計20％と履歴回避の範囲で整合）、About に 2.25 表示、上書き解除後の実日付（11/6）＝紅葉。talktest 回帰も TALK PLAYED。テスト後は日付上書きを解除済み。
- **配信**：変更4ファイル（seasonal 新規＋talk／menu／_loading_order）を WSL 配信フォルダへコピー（MD5 一致を確認）、updates2.dau を 214 レコードで再生成。更新フックで起動し、配信サーバーログで SSP が 21:34 に照合表＋全4ファイルを取得したことを確認（全て 200）。
- **nar**：v2.25 として再ビルド（`zip -D`、214エントリ＝v2.24＋季節辞書1、testzip 正常、39,959,839 bytes）。`astaroth.nar` 差し替え＋ `astaroth_v2.25_backup.nar` 保存。
- **git**：原稿＋辞書のコミット ad70ef2 を配信前に実施し、タグ v2.25 とともに push 済み（本追記の記録コミットとともに行う）。なお push は git-lfs が PATH に無いと pre-push フックで失敗する（~/workspace/bin を PATH に足して再試行し成功）。
- **実機確認（後日、ユーザー側）**：通常のランダムトークに、季節の話題（当面は紅葉プール）が時々混ざること。

## 追記30: 第3シェル「maid」（メイド服）の実装と手動ラッチ仕様（2026-11-07、nar v2.26）

ユーザーの決定（2026-11-06夜）に基づく2段構成。第1段・第2段とも完遂し、v2.26 として配信済み。衣装は2人ともクラシックな黒×白メイド（黒ドレス、白いフリルエプロン、レースのヘッドドレス）で統一。土台サンプルはアスタロト＝M1（seed 20261121）、フルフル＝M3（seed 777701、黒白版）。

- **第1段・絵の量産**（`work/gen_maid_expr.py`、WSL ComfyUI、候補と同条件 832×1216／30step／CFG4／er_sde）：土台と同シード・同衣装指定で表情指定だけを差し替える既存ワークフロー（gen_night_expr.py）で、アスタロト surface1〜5、フルフル surface11〜15 を生成（全10点 success、振り直しは下記の翼のみ）。0／10 は採用候補の生成画そのもの。フルフルには頭身指示（PROP_*）を全ジョブへ入れた。
  - **翼の振り直し1回**（`work/gen_maid_fix.py`、同シード＋翼の小ぶり指定を強化）：初回生成では 13〜15 の翼が土台（肩の後ろに小さく）より大きく広がったため再生成し、比較シート（work/maid_preview/wing_fix_compare.png）で判定した。14 は小さい翼＋明るい照れ顔になった修正版を採用。13 は大差なく初回を維持、15 は修正版で翼が消えたため初回を維持した。13／15 の翼が他面より大きめな点は、夜シェル v2.24 の 12 と同様に許容した。
- **後処理**（`work/finalize_maid.py`）：色距離キーイング＋囲み領域除去（finalize_v224.py と同一方式）。配置は両名とも一括正規化（place_group、中心統一・下端1211）。アスタロト 530×1216、フルフル 781×1216。全12面で緑残り 0px・pna＝アルファ完全一致・四隅 alpha=0。光輪内側は市松模様への合成（work/maid_preview/maid0_halo_checker.png）で透明を目視確認した。
- **シェル構築**（`shell/maid`、descript の name は `maid`）：0〜5 と 10〜15 が新規画像、それ以外（6〜9、16〜21、26〜30、46〜49、56〜59）は master の画像を仮置きコピー（ポーズ・座りの maid 版は今回作らない）。surfaces.txt は master を土台に、新規12面の当たり判定を旧 bbox → 新 bbox の線形変換で最終画像の実測に基づき付け替えた（`work/update_surfaces_maid.py`）。組み立てと静的確認は `work/assemble_maid_shell.py`：定義35＝png35＝pna35・欠けなし。
- **検品**（プレビュー `work/maid_preview/`：maid_base_all.png＝基本12面一覧、maid_height_pair.png＝2人の並列、maid_balance_compare.png＝物差し比較）：並列で頭頂・足元がほぼ揃い、フルフルの頭身は物差しの master surface17 と同じバランスに収まった。表情対応（笑顔／驚き／呆れ・拗ね／照れ／目閉じ）も両名とも成立。
- **第2段・辞書**：
  - **衣装メニュー拡張**（astaroth_menu.dic）：「衣装を変える」を3択（通常／ネグリジェ／メイド）にし、OnAstarothShellSet に maid 分岐を追加。
  - **手動ラッチ仕様**（astaroth_shell.dic v2）：手動選択を astaroth_shell_latch／astaroth_shell_latch_band（選択時点の時刻帯）に記録し、ShellDesiredName が「ラッチが現在の時刻帯で有効な間はラッチ先を返し、境目を跨いだら解除して時刻判定に戻す」よう変更。昼に選んだ装いは 23:00 の夜間帯入りで night が優先され、夜に選んだ装いはその夜間帯の間だけ維持されて 7:30 に master へ戻る。ShellSyncTag はシェル名の一般形（'Master' の正規化つき）に書き換え、maid からの復帰も扱えるようにした。ラッチが無いときの master/night 間の自動挙動は不変。テスト用フックに state のラッチ表示と latchclear を追加。
  - **看板を立てる経路への同期追加**（astaroth_signboard.dic）：SignboardSet の組み立てにも SignboardClear と同じ流儀で ShellSyncTag(0) を前置した（2026-11-06夜の実機指摘で判明した欠けへの対策。23:00 に入浴看板が立ったあと解除を挟まず 23:25 の就寝看板を立てても、挨拶の瞬間に夜シェルで現れる）。
  - About の版数を 2.26 に更新し、メイド服の一文を追加。`_loading_order.txt` は変更なし（新規辞書ファイルなし）。YAYA の規律（呼び出し結果は代入文で受ける）は全変更で遵守した。
- **検証**（WSL `~/sstp_shelltest.py` に v2.26 の19項目を追加し、全40項目 ALL PASS。旧ファイルは ~/sstp_shelltest_v225.py.bak に保存）：既存21項目（境界時刻の目標判定・同期タグ・看板解除への同梱・手動切り替え）は無変更で全合格。新規は、メニューの maid 選択肢／昼に maid を選ぶ→同期でも維持・state に maid(day)／23:00 を跨ぐ→ラッチ解除・night 優先／夜に maid を選ぶ→夜間帯内は維持・maid(night)／7:30→ラッチ解除・master 復帰タグ／23:25 に就寝看板を立てる→先頭に night 同期タグ＋就寝挨拶／看板30でもフルフルが残る（\1\s[17] あり・\1\s[-1] なし）。テスト後は「目標 master／現在 Master・ラッチなし・看板なし」に復帰済み。talktest 回帰も TALK PLAYED、OnAstarothAbout で版数 2.26 とメイドの一文を確認。
- **配信**：変更75ファイル（shell/maid 72＋辞書3）を WSL 配信フォルダへコピー（MD5 全件一致を確認）、updates2.dau を 286 レコードで再生成。更新フックで起動し、配信サーバーログで SSP が 10:35 に照合表＋全75ファイルを 200 で取得したことを確認。
- **nar**：v2.26 として再ビルド（`zip -D`、286エントリ＝v2.25 の214＋maid 72、testzip 正常、v2.25 からの欠落なし、58,102,054 bytes、MD5 ce2fb25686de0c32e5d2d53aa73a2525）。`astaroth.nar` 差し替え＋ `astaroth_v2.26_backup.nar` 保存。
- **git**：第1段のシェル構築をコミット 11f98a9、辞書変更をコミット 75a5b98 で配信前に刻み、タグ v2.26 とともに push する（本追記の記録コミットを含む）。
- **実機確認（後日、ユーザー側）**：ゴースト再起動後に、(1) シェル切り替えで「maid」が選べること（本体側リソースの前例どおり再起動が要る可能性が高い）、(2) 右クリック→おすすめ→「衣装を変える」からメイド服へ着替えられること、(3) 昼にメイドを選んだまま 23:00 を跨いだ場面と、夜に選んで 7:30 を迎えた場面の戻り、(4) メイド姿の見た目と当たり判定の位置。ポーズ・座り・看板の maid 版は仮置き（通常シェルの絵）のまま。

## 追記31: maid シェルのポーズ・座り全18面の差し替え（2026-11-07、nar v2.27）

ユーザーの指示（2026-11-07、v2.26 の実機確認でメイドシェルが「可愛い」と好評だったことを受けた続行依頼）に基づき、shell/maid で master の仮置きコピーのまま残っていたポーズ・座り全18面をメイド版に差し替えた。これで maid シェルの残る仮置きは看板 26〜30 のみ（看板は衣装と無関係なため対象外）。

- **生成**（`work/gen_maid_poses.py`、WSL ComfyUI、832×1216／30step／CFG4／er_sde）：ポーズの構図・意味づけと表情対応は gen_v223.py（夜シェルのポーズ量産）から移植し、衣装ブロックと土台シードは gen_maid_expr.py（maid 基本面）に合わせた：アスタロト＝M1（seed 20261121）、フルフル＝M3（seed 777701）。表情違い（46〜49／56〜59）は土台ポーズと同一シードで生成（maid 基本面量産の流儀）。フルフルには頭身指示（PROP_*）を全ジョブへ入れた。全18点 success、振り直しなし。
  - アスタロト：6（手を重ねる）・7（手を合わせ俯く）・8（本を抱える）・9（腕組み）と表情違い 46（笑顔）・47（目閉じ）・48（笑顔）・49（通常）、座り 20。
  - フルフル：16（身を乗り出す）・17（両手を広げて喜ぶ）・18（拗ねてそっぽ・後ろ向き）・19（お願い）と表情違い 56（照れ）・57（目閉じ）・58（驚き）・59（笑顔）、座り 21。
- **後処理**（`work/finalize_maid_poses.py`）：色距離キーイング＋囲み領域除去（finalize_maid.py と同一方式）、配置はポーズ用の単体配置（place_single、下端1211、夜ポーズと同方式）。全18面で緑残り 0px・pna＝アルファ完全一致・四隅 alpha=0。寸法はアスタロト 485〜632×1216、フルフル 598〜842×1216。キーイングで落とした微小コンポーネントは浮遊ゴミのみで、図柄の欠けがないことをプレビューで目視確認した。フルフル 16／56 の翼は大きめだが、maid 基本面 13／15（v2.26 で許容）と同傾向のため許容した。
- **当たり判定**（`work/update_surfaces_maid_poses.py`）：maid 側 surfaces.txt の対象18ブロックのみ、仮置き面（master コピー）の bbox → 新面 bbox の線形変換で最終画像の実測に基づき付け替え。他シェルには触っていない。ヘッダ注記も v2.27 の実態（残る仮置きは看板のみ）に更新した。
- **検品**（プレビュー `work/maid_pose_preview/`：maid_poses_new.png＝新規18面一覧、maid_pose_balance.png＝基本面との並列）：ポーズの意味づけ・顔・メイド衣装の一致を確認。フルフルの頭身は脚長・小顔に保たれ、アスタロトと並べても身長感が揃っている。
- **静的確認**：maid シェルは定義35＝png35＝pna35・欠け番号なし。対象18面は master 仮置きと全て相違し、非対象で master と同一なのは看板 26〜30 のみ（意図どおり）。
- **About 版数**：astaroth_menu.dic の OnAstarothAbout を 2.26 → 2.27 に（看板越し・通常の両分岐、文面は他を変更せず）。辞書変更はこの1点のみで、YAYA の規律を遵守した。
- **検証**：talktest は TALK PLAYED。新規の maid ポーズ表示テスト（WSL `~/sstp_maidpose_test.py`、9項目 ALL PASS）：実機を maid シェルへ手動切り替えしたうえで、姿勢メニュー相当の OnAstarothPoseSelect（sit／book／calm／proud／lean／joy／beg）が新規面（20・21／8／6／9／16／17／19）を表示することと、About に 2.27 が出ることを確認。shelltest は初回、自テスト（表示テスト）の手動ラッチが残った状態で時刻判定ケースを走らせたため 'desired 22:59=master' が1件 FAIL したが、これは製品側の問題ではなくテスト手順起因（ラッチ有効中は desired が maid になるのが v2.26 仕様どおり）。状態を戻して再実行し、39 PASS／0 FAIL・RESULT: ALL PASS、最終状態は「目標 master／現在 Master・ラッチなし・看板なし」に復帰済み。
- **配信**：変更38ファイル（maid 画像36＋surfaces.txt＋astaroth_menu.dic）を WSL 配信フォルダへコピー（MD5 全件一致を確認）、updates2.dau を 286 レコードで再生成。更新フックで起動し、配信サーバーログで SSP が 17:32 に照合表＋全38ファイルを 200 で取得したことを確認。
- **nar**：v2.27 として再ビルド（`zip -D`、286エントリ＝v2.26 と同一集合、testzip 正常、v2.26 からの欠落なし、57,109,921 bytes、MD5 3bb38682e063a47c2416beee0660ba7d）。`astaroth.nar` 差し替え＋ `astaroth_v2.27_backup.nar` 保存。
- **git**：コミット 8fc374f を配信前に実施し、タグ v2.27 とともに push 済み（本追記の記録コミットを含む）。なお commit 時は git-lfs を PATH（~/workspace/bin）に含める必要があった（既知の注意点）。
- **実機確認（後日、ユーザー側）**：ゴースト再起動後に、(1) 衣装を変えるでメイドにし、姿勢メニュー（座る／本を抱える／手を重ねる／腕を組む／身を乗り出す／両手を広げる／お願い）で各ポーズがメイド服で出ること、(2) つつき・撫での当たり判定の位置が新面に合っていること。
