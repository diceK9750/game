"""Illustrated word-chain duel. Pure Python rules with an injectable clock/RNG."""
import random
import time
import unicodedata
from functools import lru_cache
from typing import NamedTuple
from timed_chain import TimedChain

# Emoji are platform pictograms, not artwork copied from a commercial game.
# Finite picture names, categories and visible features. Different readings
# may share an initial; tapping still picks a continuation automatically.
CARDS = (
    ("apple", "🍎", ("りんご", "くだもの", "フルーツ", "たべもの", "しんしゅうりんご", "すりおろしりんご")),
    ("gorilla", "🦍", ("ゴリラ", "さる", "どうぶつ", "るいじんえん")),
    ("trumpet", "🎺", ("ラッパ", "がっき", "トランペット", "きんかんがっき")),
    ("panda", "🐼", ("パンダ", "くま", "どうぶつ", "ジャイアントパンダ")),
    ("daruma", "🔴", ("だるま", "おきもの", "えんぎもの", "にんぎょう")),
    ("camel", "🐪", ("らくだ", "どうぶつ", "ひとこぶらくだ")),
    ("radish", "🥕", ("にんじん", "やさい", "キャロット", "こんさい", "たべもの")),
    ("dog", "🐕", ("いぬ", "こいぬ", "どうぶつ", "ペット", "わんこ")),
    ("teddy", "🧸", ("ぬいぐるみ", "くま", "おもちゃ", "テディベア", "にんぎょう")),
    ("orange", "🍊", ("みかん", "くだもの", "フルーツ", "たべもの", "オレンジ")),
    ("turtle", "🐢", ("かめ", "りくがめ", "どうぶつ", "はちゅうるい")),
    ("glasses", "👓", ("めがね", "がんきょう", "レンズ", "フレーム")),
    ("cat", "🐈", ("ねこ", "こねこ", "どうぶつ", "ペット", "にゃんこ")),
    ("tree", "🌲", ("まつ", "き", "しょくぶつ", "じゅもく", "もみのき", "ツリー")),
    ("moon", "🌙", ("つき", "よぞら", "みかづき", "てんたい", "おつきさま")),
    ("fox", "🦊", ("きつね", "どうぶつ", "けもの", "フォックス")),
    ("mouse", "🐁", ("ねずみ", "どうぶつ", "マウス", "けもの")),
    ("ear", "👂", ("みみ", "からだ", "じかく", "ちょうかくきかん")),
    ("bee", "🐝", ("みつばち", "はち", "むし", "こんちゅう")),
    ("butterfly", "🦋", ("ちょう", "むし", "こんちゅう", "バタフライ")),
    ("rabbit", "🐇", ("うさぎ", "どうぶつ", "ラビット", "けもの")),
    ("guitar", "🎸", ("ギター", "がっき", "エレキギター", "げんがっき")),
    ("octopus", "🐙", ("たこ", "うみのいきもの", "なんたいどうぶつ", "オクトパス")),
    ("bird", "🐦", ("とり", "ことり", "どうぶつ", "バード")),
    ("squirrel", "🐿️", ("りす", "どうぶつ", "けもの")),
    ("melon", "🍉", ("すいか", "くだもの", "フルーツ", "たべもの")),
    ("umbrella", "☂️", ("かさ", "あまがさ", "ようがさ", "レイングッズ")),
    ("fish", "🐠", ("さかな", "ぎょるい", "うみのいきもの", "フィッシュ", "おさかな")),
    ("eggplant", "🍆", ("なす", "やさい", "たべもの", "しょくざい")),
    ("bell", "🔔", ("すず", "かね", "ベル", "がっき", "チャイム")),
    ("trousers", "👖", ("ズボン", "ふく", "ジーンズ", "デニム", "ボトムス")),
    ("ship", "🚢", ("ふね", "のりもの", "きせん", "シップ")),
    ("mushroom", "🍄", ("きのこ", "しょくざい", "マッシュルーム")),
    ("ice", "🧊", ("こおり", "アイスキューブ", "ロックアイス", "ひょうかい")),
    ("car", "🚗", ("くるま", "じどうしゃ", "のりもの", "マイカー")),
    ("mountain", "⛰️", ("やま", "さん", "マウンテン", "みね")),
    ("peach", "🍑", ("もも", "くだもの", "ピーチ", "フルーツ", "たべもの")),
    ("bread", "🍞", ("パン", "しょくパン", "トースト", "ブレッド", "たべもの")),
    ("lion", "🦁", ("ライオン", "どうぶつ", "しし", "けもの")),
    ("top", "🌀", ("こま", "おもちゃ", "かいてんたい", "うずまき")),
    ("pillow", "🛏️", ("まくら", "しんぐ", "ねどこ", "ベッド")),
    ("otter", "🦦", ("らっこ", "どうぶつ", "うみのいきもの")),
    ("koala", "🐨", ("コアラ", "どうぶつ", "ゆうたいるい")),
    ("ramune", "🍾", ("ラムネ", "のみもの", "たんさんいんりょう")),
    ("tie", "👔", ("ネクタイ", "ふく", "えりもと")),
    ("chair", "🪑", ("いす", "かぐ", "ざせき", "チェア")),
    ("zucchini", "🥒", ("ズッキーニ", "やさい", "たべもの", "きゅうり")),
    ("chicken", "🐔", ("にわとり", "とり", "どうぶつ")),
    ("backpack", "🎒", ("リュック", "かばん", "にもつ")),
    ("scarf", "🧣", ("マフラー", "えりまき", "ぼうかんぐ")),
    ("radio", "📻", ("ラジオ", "じゅしんき", "おんきょうきき")),
    ("riceball", "🍙", ("おにぎり", "ごはん", "たべもの")),
    ("dragon", "🐉", ("りゅう", "ドラゴン", "でんせつのいきもの", "たつ")),
    ("cow", "🐄", ("うし", "どうぶつ", "かちく")),
    ("salt", "🧂", ("しお", "ちょうみりょう", "ソルト")),
    ("plate", "🍽️", ("おさら", "しょっき", "プレート")),
    ("lavender", "🪻", ("ラベンダー", "はな", "しょくぶつ")),
    ("diamond", "💎", ("ダイヤ", "ほうせき", "きせき")),
    ("beans", "🫘", ("まめ", "しょくざい", "たね")),
    ("medaka", "🐟", ("めだか", "さかな", "ぎょるい")),
    ("sand", "🏖️", ("すな", "はまべ", "ビーチ")),
    ("pot", "🍲", ("なべ", "りょうり", "しょっき", "おなべ")),
    ("bagel", "🥯", ("ベーグル", "パン", "たべもの")),
    ("loupe", "🔍", ("ルーペ", "むしめがね", "かくだいきょう")),
    ("paint", "🎨", ("ペンキ", "とりょう", "いろ", "パレット")),
    ("knife", "🔪", ("ナイフ", "ほうちょう", "カトラリー")),
    ("tomato", "🍅", ("トマト", "やさい", "たべもの")),
    ("parsley", "🌿", ("パセリ", "ハーブ", "やさい", "かおりづけ")),
    # Five distinct pictograms cover six scarce initial sounds without
    # inventing connector-only names or changing any existing card reading.
    ("sewing_needle", "🪡", ("ぬいばり", "はり", "さいほうどうぐ")),
    ("snow_crab", "🦀", ("ズワイガニ", "かに", "シーフード")),
    ("blocks", "🧱", ("つみき", "ブロック", "おもちゃ")),
    ("golf", "⛳", ("ゴルフ", "ホール", "スポーツ")),
    ("gift", "🎁", ("プレゼント", "おくりもの", "ギフト")),
)
# New pictures strengthen common weak endings while keeping the artwork local
# to the platform emoji font. First readings cannot end with ん (start seed).
CONNECTION_CARDS = (
    ('lipstick', '💄', ('くちべに', 'リップ', 'ルージュ', 'けしょうひん', 'リップスティック')),
    ('gloves', '🧤', ('てぶくろ', 'グローブ', 'ぼうかんぐ')),
    ('snowman', '☃️', ('ゆきだるま', 'ゆき', 'スノーマン', 'せつぞう', 'ふゆ', 'スノー')),
    ('grapes', '🍇', ('ぶどう', 'グレープ', 'くだもの', 'フルーツ', 'たべもの')),
    ('curry', '🍛', ('カレーライス', 'カレー', 'ルウ', 'ライス', 'ごはん', 'たべもの')),
    ('pudding', '🍮', ('プディング', 'プリン', 'カスタード', 'おやつ', 'デザート', 'スイーツ')),
    ('thread', '🧵', ('ぬいいと', 'いとまき', 'スレッド', 'さいほう', 'いと', 'まきいと')),
    ('candle', '🕯️', ('ろうそく', 'キャンドル', 'あかり', 'ともしび', 'ほのお')),
)
CARDS += CONNECTION_CARDS

# Additional everyday names and English loanwords for existing pictures.
# Keep the original spellings and order, including persisted dictionary keys.
ADDITIONAL_READINGS = {
    'golf': ('はた', 'フラッグ', 'フラグ', 'ゴルフじょう', 'ゴルフコース', 'グリーン', 'ピン', 'はたざお', 'ゴルフのはた', 'ピンフラッグ', 'フラッグスティック', 'あな', 'カップ', 'ゴルフのホール'),
    'medaka': ('フィッシュ', 'おさかな', 'うお', 'こざかな'),
    'ramune': ('ボトル', 'びん', 'ガラスびん', 'ガラスボトル', 'シャンパン', 'シャンペン', 'スパークリングワイン', 'コルク', 'ワイン', 'ワインボトル'),
    'teddy': ('ベア', 'くまのぬいぐるみ', 'くまちゃん', 'くまさん', 'テディ', 'くまのにんぎょう', 'くまのおもちゃ', 'ベアー'),
    'glasses': ('グラッシーズ', 'アイウェア', 'スペクタクルズ', 'グラス', 'めがねのレンズ'),
    'trumpet': ('かんがっき', 'ホーン', 'きんぞくがっき', 'ブラスがっき', 'ブラス'),
    'apple': ('アップル', 'あかいりんご', 'りんごのみ', 'かじつ'),
    'camel': ('キャメル', 'さばくのふね', 'らくださん', 'ほにゅうるい', 'こぶ', 'らくだのこぶ'),
    'dog': ('ドッグ', 'わんちゃん', 'わんわん', 'かいいぬ', 'いぬころ', 'ほにゅうるい', 'いぬか', 'いぬさん', 'わん'),
    'orange': ('かんきつ', 'おみかん', 'かんきつるい', 'タンジェリン', 'マンダリン', 'シトラス', 'マンダリンオレンジ', 'かじつ'),
    'turtle': ('タートル', 'かめさん', 'こうら', 'かめのこうら', 'トータス', 'ウミガメ'),
    'cat': ('キャット', 'ねこちゃん', 'にゃんにゃん', 'かいねこ', 'ほにゅうるい', 'ねこか', 'ねこさん', 'にゃん', 'いえねこ', 'にゃー'),
    'moon': ('ムーン', 'クレセント', 'クレセントムーン', 'よるのつき', 'おつきさん', 'ゆうづき', 'ルナ'),
    'ear': ('イヤー', 'おみみ', 'みみたぶ', 'みみのあな'),
    'bee': ('ビー', 'ハニービー', 'はちさん', 'みつばちさん', 'はね', 'はちのはね'),
    'squirrel': ('スクイレル', 'しまりす', 'チップマンク', 'りすさん', 'げっしるい', 'ほにゅうるい', 'しっぽ', 'りすのしっぽ', 'リスか'),
    'melon': ('ウォーターメロン', 'カットすいか', 'すいかのひときれ', 'すいかのスライス', 'カットフルーツ', 'かじつ'),
    'umbrella': ('アンブレラ', 'こうもりがさ', 'かさのえ', 'ひがさ'),
    'fish': ('ねったいぎょ', 'トロピカルフィッシュ', 'うお'),
    'eggplant': ('エッグプラント', 'なすび', 'おなす', 'なすのじつ', 'オーバージーン', 'オーベルジーヌ', 'ベジタブル', 'おやさい'),
    'trousers': ('パンツ', 'トラウザーズ', 'ながズボン', 'ジーパン', 'デニムパンツ', 'ボトム', 'ロングパンツ', 'ようふく', 'いふく', 'ブルージーンズ', 'デニムズボン'),
    'ice': ('アイス', 'こおりのかけら', 'こおりのかたまり', 'アイスブロック', 'こおりのキューブ', 'キューブアイス'),
    'car': ('カー', 'じょうようしゃ', 'おくるま', 'じょうようじどうしゃ', 'オートモービル', 'モーターカー'),
    'top': ('スパイラル', 'うず', 'らせん', 'うずまきもよう', 'サイクロン', 'ハリケーン', 'たいふう', 'たつまき', 'ぐるぐる', 'トルネード'),
    'otter': ('オッター', 'カワウソ', 'イタチか', 'すいせいどうぶつ', 'カワウソさん', 'ほにゅうるい', 'らっこさん', 'シーオッター'),
    'tie': ('タイ', 'ワイシャツ', 'シャツ', 'えり', 'ドレスシャツ', 'ネクタイつきシャツ', 'えりつきシャツ', 'ビジネスシャツ', 'ようふく', 'いふく', 'シャツとネクタイ'),
    'chair': ('こしかけ', 'シート', 'チェアー'),
    'zucchini': ('キューカンバー', 'うり', 'ウリのなかま', 'ピクルス', 'つけもの', 'ベジタブル', 'おやさい', 'しょくざい'),
    'chicken': ('チキン', 'にわとりさん', 'にわとりのかお', 'とさか', 'くちばし'),
    'backpack': ('バックパック', 'リュックサック', 'ザック', 'ランドセル', 'スクールバッグ', 'せおいかばん', 'デイパック', 'バッグ', 'ナップザック', 'ナップサック'),
    'scarf': ('スカーフ', 'くびまき', 'ぼうかんようひん', 'ストール'),
    'radio': ('レディオ', 'かでん', 'ラジオじゅしんき', 'ポータブルラジオ'),
    'riceball': ('おむすび', 'ライスボール', 'にぎりめし', 'むすび', 'ライス', 'おこめ', 'さんかくおにぎり', 'のり', 'おにぎりののり', 'こめ', 'しろごはん'),
    'cow': ('カウ', 'ぎゅう', 'うしさん', 'ほにゅうるい', 'めうし', 'にゅうぎゅう', 'モーモー'),
    'diamond': ('ダイヤモンド', 'ジュエリー', 'ジュエル', 'ジェムストーン', 'ジェム'),
    'beans': ('ビーンズ', 'おまめ', 'まめるい', 'ビーン', 'おまめさん'),
    'sand': ('サンド', 'うみべ', 'すなはま', 'はま', 'かいがん', 'パラソル', 'ビーチパラソル', 'ひがさ', 'ビーチアンブレラ', 'うみ', 'なぎさ', 'かさ'),
    'pot': ('ポット', 'なべもの', 'スープ', 'なべりょうり', 'ホットポット', 'おなべりょうり', 'シチュー', 'にもの', 'にこみ'),
    'loupe': ('レンズ', 'かくだいレンズ', 'マグニファインググラス', 'マグニファイア'),
    'paint': ('ペイント', 'えのぐ', 'がざい', 'カラーパレット', 'えのぐのパレット', 'おえかき', 'げいじゅつ', 'え', 'アート', 'えのぐパレット'),
    'knife': ('はもの', 'キッチンナイフ', 'ちょうりきぐ', 'やいば', 'クッキングナイフ', 'ブレード'),
    'parsley': ('くさ', 'はっぱ', 'リーフ', 'パセリのは', 'みどりのはっぱ', 'バジル', 'ミント', 'は', 'やくそう', 'しょくぶつ', 'くき', 'ベジタブル', 'おやさい', 'しょくざい', 'ハーブのは', 'こうそう'),
    'sewing_needle': ('ニードル', 'ソーイングニードル', 'いと', 'さいほうばり', 'はりといと', 'ぬいもの', 'さいほう'),
    'snow_crab': ('クラブ', 'こうかくるい', 'かにさん', 'かいせん', 'かにのはさみ', 'はさみ', 'かにのつめ'),
    'blocks': ('れんが', 'ブリック', 'レンガのかべ', 'レンガづみ', 'かべ', 'レンガブロック'),
    'gift': ('はこ', 'リボン', 'プレゼントボックス', 'ギフトボックス', 'ラッピング', 'ほうそう', 'つつみ', 'ギフトラッピング', 'ほうそうがみ', 'ぞうとうひん', 'おいわい', 'つつみもの', 'ラッピングボックス'),
    'butterfly': ('ちょうちょ', 'ちょうちょう', 'はね', 'ちょうのはね', 'ウィング'),
    'plate': ('さら', 'ディッシュ', 'フォーク', 'ナイフ', 'カトラリー', 'テーブルウェア', 'フォークとナイフ'),
    'rabbit': ('バニー', 'うさちゃん', 'うさぎさん', 'ほにゅうるい', 'ペット'),
    'ship': ('せんぱく', 'おふね', 'きゃくせん', 'りょかくせん', 'クルーズシップ', 'クルーズせん',),
    'mountain': ('おやま', 'さんがく', 'やまのてっぺん', 'さんちょう', 'ちょうじょう'),
    'lavender': ('フラワー', 'ヒヤシンス', 'おはな', 'はなのくき', 'むらさきのはな', 'ヒヤシンスのはな', 'ルピナス'),
    'gorilla': ('エイプ', 'おおざる', 'ほにゅうるい', 'れいちょうるい'),
    'panda': ('パンダさん', 'くまさん', 'ほにゅうるい', 'パンダのかお', 'パンダベア'),
    'daruma': ('だるまさん', 'おきあがりこぼし'),
    'radish': ('おにんじん', 'ねやさい', 'ベジタブル', 'おやさい', 'しょくざい', 'にんじんのは'),
    'tree': ('しんようじゅ', 'じょうりょくじゅ', 'まつのき', 'もみ', 'はっぱ', 'えだ', 'みき', 'きのえだ', 'コニファー'),
    'fox': ('おきつね', 'きつねさん', 'ほにゅうるい', 'いぬか', 'きつねのかお'),
    'mouse': ('ねずみさん', 'げっしるい', 'ほにゅうるい', 'ハツカネズミ', 'チューチュー'),
    'guitar': ('エレキ', 'エレクトリックギター', 'でんきギター'),
    'octopus': ('たこのあし', 'うみのどうぶつ'),
    'bird': ('とりさん', 'ちょうるい', 'つばさ', 'はね', 'ウィング', 'くちばし'),
    'bell': ('ハンドベル',),
    'mushroom': ('きのこるい', 'きのこのかさ', 'ファンガス', 'きのこのじく'),
    'peach': ('もものみ', 'かじつ'),
    'lion': ('ひゃくじゅうのおう', 'たてがみ', 'ねこか', 'ほにゅうるい', 'ライオンのかお'),
    'pillow': ('しんだい', 'マットレス', 'ふとん', 'シーツ'),
    'koala': ('コアラちゃん', 'ほにゅうるい', 'コアラのかお', 'こもりぐま', 'きのぼりふくろぐま', 'ふくろぐま', 'コアラベア'),
    'salt': ('しおいれ', 'しおびん', 'ソルトシェイカー', 'ソルトシェーカー', 'しおのいれもの'),
    'bagel': ('ベーグルパン', 'リングパン', 'まるいパン'),
    'tomato': ('トメイト', 'トメート', 'あかいトマト', 'トマトのみ', 'くだもの', 'フルーツ', 'かじつ', 'ベジタブル', 'おやさい', 'しょくざい'),
    'lipstick': ('リップカラー', 'べに', 'ぼうべに', 'コスメ',),
    'gloves': ('てぶくろのペア', 'てぶくろのセット'),
    'snowman': ('ゆきのだるま', 'ゆきにんぎょう'),
    'grapes': ('ぶどうのふさ', 'ぶどうのみ', 'かじつ', 'ぶどうのつぶ'),
    'curry': ('カレーソース', 'カレーとごはん', 'ライスカレー', 'カリー', 'カレールー', 'カレールウ'),
    'pudding': ('カスタードプリン', 'カラメルプリン', 'おかし', 'ようがし', 'フラン'),
    'thread': ('ソーイングスレッド', 'ミシンいと', 'ボビン', 'スプール', 'いとのボビン'),
    'candle': ('キャンドルライト', 'ろうそくのひ', 'キャンドルのひ'),
    'bread': ('ローフ', 'スライスパン', 'スライスブレッド'),
}
CARDS = tuple((identity, icon, words + ADDITIONAL_READINGS.get(identity, ()))
              for identity, icon, words in CARDS)

# Broad categories, remote associations and discovery-style names remain valid
# dictionary entries, but should not beat a natural picture name on a tap.
SPECIAL_READINGS = frozenset({
    'くだもの', 'フルーツ', 'たべもの', 'どうぶつ', 'やさい', 'おもちゃ',
    'しょくぶつ', 'けもの', 'うみのいきもの', 'むし', 'ぎょるい', 'がっき',
    'ふく', 'のりもの', 'しょくざい', 'のみもの', 'しょっき', 'はな',
    'かちく', 'りょうり', 'ペット', 'こんちゅう', 'たね', 'ほうせき',
    'しんしゅうりんご', 'すりおろしりんご', 'るいじんえん',
    'きんかんがっき', 'ひとこぶらくだ', 'えんぎもの', 'おきもの',
    'はちゅうるい', 'じかく', 'ちょうかくきかん', 'なんたいどうぶつ',
    'げんがっき', 'かいてんたい', 'しんぐ', 'かぐ', 'ぼうかんぐ',
    'レイングッズ', 'でんせつのいきもの', 'ゆうたいるい',
    'たんさんいんりょう', 'かくだいきょう', 'かおりづけ',
    'さいほうどうぐ', 'シーフード', 'ホール', 'スポーツ',
    # Broad classifications remain valid but lose ties to familiar names.
    'ほにゅうるい', 'げっしるい', 'ちょうるい', 'こうかくるい',
    'ねこか', 'すいせいどうぶつ', 'うみのどうぶつ', 'かんきつるい',
    'かじつ', 'ねやさい', 'きのこるい', 'まめるい', 'ウリのなかま',
    'しんようじゅ', 'じょうりょくじゅ', 'きんぞくがっき',
    'ちょうりきぐ', 'かでん', 'ぼうかんようひん', 'かいせん',
    'いぬか', 'ねこか', 'ようふく', 'いふく', 'テーブルウェア',
    'カットフルーツ', 'つけもの', 'ピクルス', 'シチュー', 'にもの',
    'にこみ', 'やくそう', 'バジル', 'ミント', 'ぞうとうひん',
    'れいちょうるい', 'リスか', 'ブラス', 'おえかき', 'げいじゅつ',
    'ぬいもの', 'おいわい', 'たつまき', 'ウミガメ', 'にゅうぎゅう',
    'ワイン', 'ワインボトル',
    'ベジタブル', 'おやさい', 'え', 'アート', 'さいほう', 'あな', 'カップ',
    'ぐるぐる', 'ルピナス', 'ゆうづき', 'きのぼりふくろぐま', 'ふくろぐま',
    'ふゆ', 'おやつ', 'デザート', 'スイーツ',
    'てぶくろのペア', 'ぶどうのふさ', 'ろうそくのひ',
    'コスメ', 'おかし', 'ようがし', 'ボビン', 'スプール',
    'コニファー', 'にゃー', 'きのこのじく', 'ぶどうのつぶ', 'てぶくろのセット', 'ハーブのは', 'いとのボビン', 'カレーとごはん', 'こおりのキューブ', 'みみのあな',
    'ルナ', 'チューチュー', 'モーモー', 'フラン',
    'カレールー', 'カレールウ', 'ゆきにんぎょう', 'めがねのレンズ', 'にんじんのは', 'はちのはね', 'くまのおもちゃ', 'ゴルフのホール', 'キャンドルのひ',
    'トルネード', 'ブレード', 'シャツとネクタイ',
})


def reading_kind(word):
    return 'special' if word in SPECIAL_READINGS else 'common'


def reading_connections(cards=CARDS):
    """Catalog graph: distinct *other* card identities, never word counts."""
    heads = {card[0]: {head(word) for word in card[2] if tail(word) != 'ん'} for card in cards}
    return {(card[0], word): sum(tail(word) in h and identity != card[0]
                                  for identity, h in heads.items())
            for card in cards for word in card[2] if tail(word) != 'ん'}
# Indivisible display-reading block in every initial certified route.
PERFECT_CANONICAL_SEGMENT = (
    ('tomato', 'トマト'), ('bird', 'とり'), ('apple', 'りんご'),
    ('gorilla', 'ゴリラ'), ('trumpet', 'ラッパ'), ('parsley', 'パセリ'),
)
# Certified fallback spine, not a freely rotating ring: rotation could split
# the canonical block. Retain the existing name for the catalog witness.
PERFECT_RING = (
    'tomato', 'bird', 'apple', 'gorilla', 'trumpet', 'parsley',
    'squirrel', 'bell', 'zucchini', 'chicken', 'backpack', 'car',
    'scarf', 'radio', 'riceball', 'dragon', 'cow', 'salt', 'plate', 'lavender',
    'diamond', 'mountain', 'beans', 'medaka', 'umbrella', 'fish', 'eggplant',
    'sand', 'pot', 'bagel', 'loupe', 'paint', 'mushroom', 'koala', 'camel',
    'daruma', 'tree', 'moon', 'fox', 'mouse', 'bee', 'butterfly', 'rabbit',
    'guitar', 'octopus', 'top', 'pillow', 'otter', 'ice',
)
# Two validated 48-card fallback witnesses. The opening board contains all
# eight connector pictures; the random choice keeps the older pictures varied.
# Each witness is checked against the actual refill rules before play starts.
FALLBACK_48_ROUTES = (
    PERFECT_CANONICAL_SEGMENT + (
        ('lipstick', 'リップ'), ('pudding', 'プディング'), ('gloves', 'グローブ'),
        ('grapes', 'ぶどう'), ('sand', 'うみべ'), ('bagel', 'ベーグル'),
        ('curry', 'ルウ'), ('butterfly', 'ウィング'), ('glasses', 'グラッシーズ'),
        ('zucchini', 'ズッキーニ'), ('daruma', 'にんぎょう'), ('rabbit', 'うさぎ'),
        ('gift', 'ギフト'), ('fish', 'トロピカルフィッシュ'), ('snowman', 'ゆき'),
        ('candle', 'キャンドルライト'), ('turtle', 'トータス'), ('thread', 'スレッド'),
        ('tie', 'ドレスシャツ'), ('blocks', 'つみき'), ('radish', 'キャロット'),
        ('paint', 'とりょう'), ('top', 'うずまきもよう'), ('cow', 'うし'),
        ('pillow', 'しんだい'), ('dog', 'いぬ'), ('sewing_needle', 'ぬいばり'),
        ('backpack', 'リュック'), ('moon', 'クレセント'), ('trousers', 'トラウザーズ'),
        ('snow_crab', 'ズワイガニ'), ('cat', 'にゃんこ'), ('koala', 'コアラのかお'),
        ('riceball', 'おにぎり'), ('squirrel', 'りす'), ('melon', 'すいか'),
        ('plate', 'カトラリー'), ('dragon', 'りゅう'), ('medaka', 'うお'),
        ('eggplant', 'おなす'), ('scarf', 'ストール'), ('loupe', 'ルーペ'),
    ),
    PERFECT_CANONICAL_SEGMENT + (
        ('lipstick', 'リップ'), ('pudding', 'プディング'), ('grapes', 'グレープ'),
        ('gift', 'プレゼントボックス'), ('thread', 'スレッド'), ('dog', 'ドッグ'),
        ('gloves', 'グローブ'), ('blocks', 'ブロック'), ('snow_crab', 'クラブ'),
        ('trousers', 'ブルージーンズ'), ('zucchini', 'ズッキーニ'), ('riceball', 'にぎりめし'),
        ('pillow', 'しんだい'), ('sewing_needle', 'いと'), ('fish', 'トロピカルフィッシュ'),
        ('snowman', 'ゆき'), ('candle', 'キャンドル'), ('curry', 'ルウ'),
        ('sand', 'うみ'), ('bee', 'みつばち'), ('chair', 'チェア'),
        ('umbrella', 'あまがさ'), ('mountain', 'さんちょう'), ('medaka', 'うお'),
        ('moon', 'おつきさま'), ('tree', 'まつのき'), ('mushroom', 'きのこ'),
        ('koala', 'コアラベア'), ('glasses', 'アイウェア'), ('ice', 'アイスブロック'),
        ('scarf', 'くびまき'), ('diamond', 'きせき'), ('fox', 'きつね'),
        ('cat', 'ねこ'), ('ramune', 'コルク'), ('panda', 'くま'),
        ('loupe', 'マグニファインググラス'), ('melon', 'すいかのひときれ'), ('radio', 'レディオ'),
        ('octopus', 'オクトパス'), ('pot', 'スープ'), ('plate', 'プレート'),
    ),
)
SMALL = str.maketrans("ゃゅょぁぃぅぇぉっゎ", "やゆよあいうえおつわ")

# Durable miss outline (~1.2s): parity with numbers WRONG_EFFECT_FRAMES (~72 @ 60fps).
# Short-landscape status truncates the miss copy, so the wrong card itself must stay marked.
MISS_OUTLINE_SECONDS = 1.2


@lru_cache(maxsize=2048)
def normalize_reading(word):
    """Comparison key only; never replace a display/history reading with it.

    NFC joins voiced kana. Keep internal small kana and long marks (different
    words must not collapse); head/tail apply the house boundary rules.
    """
    return ''.join(chr(ord(c) - 0x60) if 'ァ' <= c <= 'ヶ' else c
                   for c in unicodedata.normalize('NFC', word))


@lru_cache(maxsize=2048)
def head(word):
    return normalize_reading(word)[:1].translate(SMALL)


@lru_cache(maxsize=2048)
def tail(word):
    """House rule: long marks use preceding kana; small kana become full-size."""
    return normalize_reading(word).rstrip("ー")[-1:].translate(SMALL)


@lru_cache(maxsize=4096)
def _readings_from(card, required):
    """Catalog-local cache; no board/stock state is retained here."""
    return tuple((word, normalize_reading(word)) for word in card[2]
                 if head(word) == required and tail(word) != 'ん')


def chain_moves(cards, required, seen):
    """Pure legal-move enumeration; None is a consumed board slot."""
    required = head(required)
    seen = {normalize_reading(w) for w in seen}
    return [(i, word) for i, card in enumerate(cards) if card is not None
            for word, key in _readings_from(card, required) if key not in seen]


# Keep initial certified deals stable; these aliases remain playable and discoverable.
INITIAL_ROUTE_EXTRA_READINGS = frozenset((('dog', 'わんこ'), ('cat', 'にゃんこ'), ('chair', 'チェア'), ('tree', 'ツリー'), ('moon', 'おつきさま'), ('paint', 'パレット'), ('pillow', 'ベッド'), ('dragon', 'たつ'), ('top', 'うずまき'))) | frozenset(
    (identity, word) for identity, words in ADDITIONAL_READINGS.items() for word in words
)

def starting_route(required, total, seen, rng, node_budget=256, allow_lipstick=False, allow_extra=False):
    """Bounded randomized chain with the six-card block as one atomic edge."""
    reserved = {identity for identity, _ in PERFECT_CANONICAL_SEGMENT}
    by_head = {}
    for card in CARDS:
        if card[0] in reserved:
            continue
        for word in card[2]:
            if ((card[0], word) not in INITIAL_ROUTE_EXTRA_READINGS or (allow_lipstick and (card[0], word) == ('lipstick', 'リップカラー') or allow_extra and (card[0], word) in (('curry', 'カリー'), ('thread', 'スプール'), ('grapes', 'ぶどうのみ')))) and tail(word) != 'ん':
                by_head.setdefault(head(word), []).append(((card[0], word),))
    by_head.setdefault('と', []).append(PERFECT_CANONICAL_SEGMENT)
    connector_ids = {card[0] for card in CONNECTION_CARDS} if total == 48 else frozenset()
    nodes = 0

    def search(required, route, ids, words):
        nonlocal nodes
        if len(route) == total:
            return route if reserved <= ids else None
        if nodes >= node_budget:
            return None
        nodes += 1
        choices = list(by_head.get(required, ()))
        rng.shuffle(choices)
        # Preserve random order within each group; promote newer pictures only
        # for 48-card starts, without changing any move or fallback rule.
        if connector_ids:
            choices.sort(key=lambda block: block[0][0] in connector_ids, reverse=True)
        for block in choices:
            new_ids = {identity for identity, _ in block}
            new_words = {normalize_reading(word) for _, word in block}
            if new_ids & ids or new_words & words or len(route) + len(block) > total:
                continue
            if not reserved <= (ids | new_ids) and total - len(route) - len(block) < 6:
                continue
            found = search(tail(block[-1][1]), route + list(block), ids | new_ids, words | new_words)
            if found is not None:
                return found
            if nodes >= node_budget:
                break
        return None

    return search(head(required), [], set(), {normalize_reading(w) for w in seen})


def chain_step(cards, stock, seen, move):
    """Simulate the real refill/rescue rules without touching the live round."""
    i, word = move
    cards, stock = list(cards), list(stock)
    seen = {normalize_reading(w) for w in seen} | {normalize_reading(word)}
    required = tail(word)
    cards[i] = stock.pop(0) if stock else None
    if cards[i] is not None and not chain_moves(cards, required, seen):
        for j, card in enumerate(stock):
            if chain_moves((card,), required, seen):
                cards[i], stock[j] = card, cards[i]
                break
    return tuple(cards), tuple(stock), required, frozenset(seen)


def longest_chain_move(cards, stock, required, seen, node_budget=4096):
    """Cooperative longest continuation, with a fair bounded search per root.

    A full route is a proof of possibility, not a prediction of player input.
    On cutoff, scores are achieved path lengths, never invented exact optima.
    """
    required = head(required)
    initial = (tuple(cards), tuple(stock), required, frozenset(normalize_reading(w) for w in seen))
    candidates = chain_moves(initial[0], required, initial[3])
    if not candidates:
        return None, {"length": 0, "perfect": False, "exact": True, "nodes": 0, "route": ()}
    remaining = sum(c is not None for c in cards) + len(stock)
    per_move = max(1, node_budget // len(candidates))
    best_move, best_length, total_nodes, all_exact = candidates[0], 0, 0, True
    best_route = ()
    for move in candidates:
        memo, nodes = {}, 0

        def search(state):
            nonlocal nodes
            if state in memo:
                return memo[state], True
            if nodes >= per_move:
                return (), False
            nodes += 1
            board, deck, head, words = state
            bound = sum(c is not None for c in board) + len(deck)
            options = chain_moves(board, head, words)
            best, exact = (), True
            for option in options:
                suffix, complete = search(chain_step(board, deck, words, option))
                route = (option,) + suffix
                if len(route) > len(best):
                    best = route
                exact = exact and complete
                if len(best) == bound:
                    memo[state] = best
                    return best, True
                if nodes >= per_move:
                    exact = False
                    break
            if exact:
                memo[state] = best
            return best, exact

        suffix, exact = search(chain_step(initial[0], initial[1], initial[3], move))
        route = (move,) + suffix
        length = len(route)
        total_nodes += nodes
        all_exact = all_exact and exact
        if length > best_length:
            best_move, best_length = move, length
            best_route = route
        if length == remaining:
            return move, {"length": length, "perfect": True, "exact": True, "nodes": total_nodes, "route": route}
    return best_move, {"length": best_length, "perfect": False, "exact": all_exact, "nodes": total_nodes, "route": best_route}


class PerfectStep(NamedTuple):
    identity: str
    reading: str
    key: str
    required: str


def certify_route(state, identity_route):
    """Resolve identities on the current board, replay refill, prove exhaustion.

    Never infer availability from board+stock membership alone: a connector
    stranded in stock must actually become visible under chain_step's rules.
    """
    witnesses = []
    for identity, word in identity_route:
        move = next((m for m in chain_moves(state[0], state[2], state[3])
                     if state[0][m[0]][0] == identity and m[1] == word), None)
        if move is None:
            return None
        witnesses.append((state, move, PerfectStep(identity, word, normalize_reading(word), tail(word))))
        state = chain_step(state[0], state[1], state[3], move)
    return witnesses if not any(state[0]) and not state[1] else None


class ShiritoriRound:
    CPU_CONTINUE_CHANCE = {'easy': .10, 'normal': .65, 'hard': .90}
    CPU_MAX_STREAK = {'easy': 2, 'normal': 3, 'hard': 5}
    CPU_ANSWER_DELAY = 2.2
    CPU_UPDATE_SLACK = .25  # Leave time for a delayed browser frame before combo expiry.
    CPU_FEVER_HOLD = 1.2  # Below the seventh-hit 1.8-second combo window.
    RIVAL_STYLE_LABELS = {'chain': '連鎖型', 'speed': '速攻型', 'counter': '反撃型'}
    # (continuation chance, maximum streak, answer delay).
    RIVAL_PROFILES = {
        'chain': {'easy': (.10, 2, 2.2), 'normal': (.65, 3, 2.2), 'hard': (.90, 5, 2.2)},
        'speed': {'easy': (.05, 2, 2.0), 'normal': (.40, 2, 1.6), 'hard': (.70, 4, 1.3)},
        'counter': {'easy': (.05, 2, 2.2), 'normal': (.50, 3, 2.2), 'hard': (.75, 5, 2.2)},
    }
    COUNTER_PROFILES = {'easy': (.15, 2, 2.2), 'normal': (.80, 5, 2.2), 'hard': (.95, 7, 2.2)}

    def __init__(self, difficulty="normal", rng=None, clock=None, mode="battle", total=24,
                 rival_style="chain"):
        self.rng = rng or random.Random()
        self.clock = clock or time.monotonic
        self.difficulty = difficulty if difficulty in ("easy", "normal", "hard") else "normal"
        self.rival_style = rival_style if rival_style in self.RIVAL_STYLE_LABELS else 'chain'
        self.limit = {"easy": 30, "normal": 20, "hard": 12}[self.difficulty]
        self.phase = "intro"
        self.mode = mode if mode in ("battle", "solo") else "battle"
        self.total = total if type(total) is int and total in (12, 24, 36, 48) else 24
        self.stock = []
        self.seen = set()
        self.relinks = 2
        self.resume_phase = "playing"
        self.refilled = None
        self.break_next = False
        self.cards = []
        self.discoveries = set()  # Retain earned readings across pause/restart snapshots.
        self.history = []
        self.used = {}
        self.message = "絵をタップ！つながる読み方を自動で選ぶよ。"
        self.required = "り"
        self.last_word = "しりとり"
        self.selected = None
        self.mistakes = 0
        self.miss_card = None
        self.miss_until = 0
        self.hints = 3
        self.hint = None
        self.winner = None
        self.perfect = False
        self.turn = "you"
        self.deadline = 0
        self.saved_remaining = 0
        self.combo_owner = None
        self.cpu_due = 0
        self.saved_cpu_remaining = 0
        self.revision = 0
        self.cpu_move = None
        self.counter_ready = False
        self.counter_active = False
        self.counter_event = 0
        self.cpu_fever_hold = False
        self._chain_advice = {}
        self.perfect_route = ()  # Identity-based certificate, never sent to UI.
        self.initial_perfect_route = ()
        self.chain = TimedChain(self.clock())

    def start(self):
        self.chain = TimedChain(self.clock())
        self.counter_ready = self.counter_active = False
        self.counter_event = 0
        self.cpu_fever_hold = False
        self._chain_advice.clear()
        by_id = {card[0]: card for card in CARDS}
        seed = self.rng.choice(CARDS)[2][0]
        snapshot = self.rng.getstate() if self.total == 48 else None
        route_words = starting_route(tail(seed), self.total, {seed}, self.rng)
        if (self.total == 48 and route_words is not None
                and any(identity in {card[0] for card in CONNECTION_CARDS}
                        for identity, _ in route_words[:24])):
            newer = {card[0] for card in CONNECTION_CARDS}
            def rank(route):
                return (len({identity for identity, _ in route} & newer),
                        len({identity for identity, _ in route[:24]} & newer))
            retry_rng = random.Random()
            retry_rng.setstate(snapshot)
            candidate = starting_route(tail(seed), self.total, {seed}, retry_rng, allow_lipstick=True)
            if candidate is not None:
                candidate_total, candidate_visible = rank(candidate)
                original_total, original_visible = rank(route_words)
                if (candidate_total >= original_total and candidate_visible >= original_visible
                        and (candidate_total > original_total or candidate_visible > original_visible)):
                    route_words = candidate
            # The extra search uses the same random state and cannot reduce either count.
            if rank(route_words) != (len(newer), len(newer)):
                extra_rng = random.Random()
                extra_rng.setstate(snapshot)
                extra = starting_route(tail(seed), self.total, {seed}, extra_rng,
                                       allow_lipstick=True, allow_extra=True)
                if extra is not None:
                    extra_total, extra_visible = rank(extra)
                    best_total, best_visible = rank(route_words)
                    if (extra_total >= best_total and extra_visible >= best_visible
                            and (extra_total > best_total or extra_visible > best_visible)):
                        route_words = extra
        # A 48-card round should visibly offer a newer connector even when a
        # successful search happens to place every one of them in the stock.
        if self.total == 48 and route_words is not None:
            connector_ids = {card[0] for card in CONNECTION_CARDS}
            if not any(identity in connector_ids for identity, _ in route_words[:24]):
                route_words = None
        if route_words is None:
            seed = 'トースト'
            if self.total == 48:
                route_words = list(self.rng.choice(FALLBACK_48_ROUTES))
            else:
                route_words = [(key, by_id[key][2][0]) for key in PERFECT_RING[:self.total]]
        chosen = [by_id[key] for key, _ in route_words]
        self.cards, self.stock = chosen[:24], chosen[24:]
        self.rng.shuffle(self.cards)
        self.used = {}
        self.history = []
        self.last_word, self.required = seed, tail(seed)
        self.seen = {normalize_reading(seed)}
        self.turn, self.phase = "you", "playing"
        self.combo_owner = None
        self.cpu_due = 0
        self.winner = None
        self.perfect = False
        self.cpu_move = None
        self.selected = self.hint = None
        self.mistakes, self.hints = 0, 3
        self.miss_card = None
        self.miss_until = 0
        self.relinks = 2
        self.refilled = None
        self.break_next = False
        self.message = f"「{self.required}」から始まる絵をさがそう。"
        self.deadline = self.clock() + self.limit
        # Replay the witness using the same transition rules as planning.
        state = (tuple(self.cards), tuple(self.stock), self.required, frozenset(self.seen))
        witnesses = certify_route(state, route_words)
        if witnesses is None:
            raise ValueError('Invalid perfect starting route or refill witness')
        self.remember_perfect(witnesses)
        self.initial_perfect_route = self.perfect_route
        self.revision += 1

    def moves(self):
        return chain_moves(tuple(None if i in self.used else c for i, c in enumerate(self.cards)),
                           self.required, self.seen)

    def capture_counts(self):
        """History is the sole source of capture totals (including replaced slots)."""
        return (sum(step.get('owner') == 'you' for step in self.history),
                sum(step.get('owner') == 'cpu' for step in self.history))

    def winner_by_captures(self):
        if self.mode == 'solo':
            return 'you'
        you, cpu = self.capture_counts()
        return 'you' if you > cpu else 'cpu' if cpu > you else 'draw'

    def choose_move_for_card(self, index):
        """Choose a reading against the actual board/stock/seen after refill.

        A current certified full route wins. Otherwise, if several readings
        match, compare short witnessed continuations before the existing
        common-reading and next-card tie-break. Single-reading taps never run
        a bounded search. A cutoff does not prove the chosen route optimal.
        """
        board = tuple(None if i in self.used else c for i, c in enumerate(self.cards))
        state = (board, tuple(self.stock), head(self.required),
                 frozenset(normalize_reading(w) for w in self.seen))
        candidates = [move for move in chain_moves(board, state[2], state[3]) if move[0] == index]
        if not candidates:
            return None
        proof = self._chain_advice.get(state)
        # If the chosen card occurs later in a known certificate, try moving
        # only that card to the front. Accept it solely after replaying the
        # entire route with the actual board, stock, seen words and refill.
        if (not proof or proof[0] not in candidates) and self.perfect_route and isinstance(self.perfect_route[0], PerfectStep) and board[index] is not None:
            remaining_ids = {c[0] for c in board + tuple(self.stock) if c is not None}
            suffix = [(s.identity, s.reading) for s in self.perfect_route if s.identity in remaining_ids]
            chosen_id = board[index][0]
            if suffix and {i for i, _ in suffix} == remaining_ids and chosen_id in remaining_ids:
                rest = [(identity, word) for identity, word in suffix if identity != chosen_id]
                for move in candidates:
                    witnesses = certify_route(state, [(chosen_id, move[1])] + rest)
                    if witnesses:
                        self.remember_perfect(witnesses)
                        proof = self._chain_advice.get(state)
                        break
        # A hint/CPU plan contains an actually reached route even when bounded
        # search could not prove it perfect. Tapping its card must use the same
        # reading; a cutoff is still unknown, never proof of impossibility.
        if proof and proof[0] in candidates:
            return proof[0]

        def score(move):
            next_board, _, required, seen = chain_step(state[0], state[1], state[3], move)
            next_cards = {next_board[i][0] for i, _ in chain_moves(next_board, required, seen)}
            connected = bool(next_cards) or not any(next_board) and not state[1]
            common = reading_kind(move[1]) == 'common'
            return (2 if common and connected else 1 if connected else 0,
                    len(next_cards), common, -candidates.index(move))

        if len(candidates) == 1:
            return candidates[0]

        def projected(move):
            next_board, next_stock, required, seen = chain_step(state[0], state[1], state[3], move)
            if not any(next_board) and not next_stock:
                return (1, 1, score(move))
            _, plan = longest_chain_move(next_board, next_stock, required, seen, node_budget=48)
            # Only achieved path lengths are compared. A cutoff is unknown.
            return (int(plan['perfect']), plan['length'], score(move))

        return max(candidates, key=projected)

    def finish(self, winner, reason):
        self.phase, self.winner, self.message = "finished", winner, reason
        self.selected = self.hint = None
        self.miss_card = None
        self.miss_until = 0
        self.chain.sync(self.clock(), ())
        self.combo_owner = None
        self.counter_ready = self.counter_active = False
        self.cpu_fever_hold = False
        self.revision += 1

    def remaining(self):
        return max(0, self.saved_remaining if self.phase == "paused" else self.deadline - self.clock())

    def combo_remaining(self):
        if self.combo_owner is None:
            return 0.0
        return self.chain.players[self.combo_owner]['remaining']

    def cpu_profile(self):
        if self.rival_style == 'counter' and self.counter_active and self.mode == 'battle':
            return self.COUNTER_PROFILES[self.difficulty]
        return self.RIVAL_PROFILES[self.rival_style][self.difficulty]

    def cpu_delay(self):
        delay = self.cpu_profile()[2]
        # Only the powered hard counter can reach seven. Keep published styles
        # unchanged and schedule its late answers inside the shared time window.
        if self.rival_style == 'counter' and self.counter_active and self.difficulty == 'hard':
            if self.cpu_fever_hold:
                return self.CPU_FEVER_HOLD
            count = self.chain.players['cpu']['count']
            if self.combo_owner == 'cpu' and count > 0:
                delay = min(delay, TimedChain.window(count) - self.CPU_UPDATE_SLACK)
        return delay

    def cpu_should_continue_combo(self):
        """Decide once after a CPU hit; answer quality stays with chain_advice()."""
        if self.mode != 'battle' or self.turn != 'cpu' or self.combo_owner != 'cpu':
            return False
        count = self.chain.players['cpu']['count']
        chance, maximum, delay = self.cpu_profile()
        if count >= maximum:
            return False
        if self.combo_remaining() <= delay:
            return False
        return self.rng.random() < chance

    def handoff(self):
        """Pass a completed combo without treating it as a miss or timeout."""
        owner = self.turn
        self.chain.miss(owner)
        self.combo_owner = None
        self.cpu_fever_hold = False
        self.turn = 'cpu' if owner == 'you' else 'you'
        if owner == 'cpu':
            self.counter_active = False
        elif self.rival_style == 'counter' and self.counter_ready and self.mode == 'battle':
            self.counter_ready = False
            self.counter_active = True
            self.counter_event += 1
        now = self.clock()
        self.deadline = now + (self.cpu_delay() if self.turn == 'cpu' else self.limit)
        self.cpu_due = self.deadline if self.turn == 'cpu' else 0
        self.cpu_move = None
        self.message = ('COUNTER! ルナが反撃します！' if self.counter_active else 'ルナの番。つながる絵を探しています…') if self.turn == 'cpu' else 'あなたの番。つながる絵を探そう！'
        self.revision += 1
        if self.turn == 'cpu':
            self.prepare_cpu()
        self.chain.sync(now, (self.turn,) if self.phase == 'playing' else ())

    def update(self):
        now = self.clock()
        self.chain.sync(now, (self.turn,) if self.phase == 'playing' else ())
        if self.phase != "playing":
            return
        if self.mode == "solo":
            return
        if self.combo_owner is not None:
            if self.combo_remaining() <= 0:
                self.handoff()
                return
            if self.turn == 'cpu' and now >= self.cpu_due:
                if self.cpu_fever_hold:
                    self.handoff()
                    return
                if self.cpu_move is None:
                    self.prepare_cpu()
                if self.cpu_move is not None:
                    self.take(*self.cpu_move)
            return
        if self.turn == "you" and self.remaining() <= 0:
            self.finish("cpu", "時間切れ。次は読み方の候補も使ってみよう！")
        elif self.turn == "cpu":
            if self.cpu_move is None:
                self.prepare_cpu()
            if now >= self.cpu_due and self.cpu_move is not None:
                self.take(*self.cpu_move)

    def prepare_cpu(self):
        moves = self.moves()
        if not moves:
            self.finish(self.winner_by_captures(), "つながる絵がなくなった！取得枚数で勝敗を判定。")
            return
        self.cpu_move, self.cpu_plan = self.chain_advice()

    def remember_perfect(self, witnesses):
        """Install only a fully replayed proof, with exact-state suffix caches."""
        self._chain_advice.clear()
        self.perfect_route = tuple(step for _, _, step in witnesses)
        route = tuple(move for _, move, _ in witnesses)
        for i, (state, move, _) in enumerate(witnesses):
            self._chain_advice[state] = (move, {'length': len(route)-i, 'perfect': True,
                'exact': True, 'nodes': 0, 'route': route[i:], 'witness': self.perfect_route[i:]})

    def chain_advice(self):
        """Exact proof first, identity re-sync second, bounded replanning last.

        A search cutoff is UNKNOWN, not proof that perfect is impossible.
        Display/history spelling never participates in the state comparison.
        """
        board = tuple(None if i in self.used else c for i, c in enumerate(self.cards))
        state = (board, tuple(self.stock), head(self.required), frozenset(normalize_reading(w) for w in self.seen))
        if state in self._chain_advice:
            return self._chain_advice[state]
        remaining_ids = {c[0] for c in board + tuple(self.stock) if c is not None}
        suffix = [(s.identity, s.reading) for s in self.perfect_route if s.identity in remaining_ids]
        if suffix and {identity for identity, _ in suffix} == remaining_ids:
            # Also accept another reading of the next picture (apple: し/す -> ご).
            # Each candidate is replayed to the end; matching tails alone is not proof.
            candidates = [suffix] + [[(suffix[0][0], word)] + suffix[1:]
                for i, word in chain_moves(board, state[2], state[3])
                if board[i][0] == suffix[0][0] and word != suffix[0][1]]
            for candidate in candidates:
                witnesses = certify_route(state, candidate)
                if witnesses:
                    self.remember_perfect(witnesses)
                    return self._chain_advice[state]
        self._chain_advice.clear()
        move, plan = longest_chain_move(*state)
        self._chain_advice[state] = (move, plan)
        if plan['perfect']:
            replay, identities = state, []
            for index, word in plan['route']:
                identities.append((replay[0][index][0], word))
                replay = chain_step(replay[0], replay[1], replay[3], (index, word))
            self.remember_perfect(certify_route(state, identities))
        return move, plan

    def best_relink(self):
        """Choose a witnessed continuation, not a claim of optimality.

        This runs only for the player's blocked solo round. Each distinct
        initial gets a small bounded search, using the same stock/refill rules.
        The selected move and reading are cached for the highlighted card.
        """
        board = tuple(None if i in self.used else c for i, c in enumerate(self.cards))
        stock = tuple(self.stock)
        seen = frozenset(normalize_reading(w) for w in self.seen)
        initials = sorted({head(word) for card in board if card is not None
                           for word in card[2]
                           if tail(word) != 'ん' and normalize_reading(word) not in seen})
        best = None
        for initial in initials:
            move, plan = longest_chain_move(board, stock, initial, seen, node_budget=32)
            if move is None:
                continue
            if best is None or (plan['perfect'], plan['length']) > (best[2]['perfect'], best[2]['length']):
                best = (initial, move, plan)
            if plan['perfect']:
                break
        if best is None:
            return None
        initial, move, plan = best
        state = (board, stock, initial, seen)
        # Non-perfect plans are actual witnessed routes but may be incomplete.
        # Never present a bounded cutoff as a proof that no longer route exists.
        self._chain_advice.clear()
        if plan['perfect']:
            replay, identities = state, []
            for index, word in plan['route']:
                identities.append((replay[0][index][0], word))
                replay = chain_step(replay[0], replay[1], replay[3], (index, word))
            witnesses = certify_route(state, identities)
            if witnesses:
                self.remember_perfect(witnesses)
            else:
                self._chain_advice[state] = (move, dict(plan, perfect=False, exact=False))
        else:
            self._chain_advice[state] = (move, plan)
        return initial, move

    def take(self, index, word):
        owner = self.turn
        self.chain.hit(owner, self.clock())
        if owner == 'you' and self.mode == 'battle' and self.rival_style == 'counter' and self.chain.players['you']['count'] >= 4:
            self.counter_ready = True
        if self.mode == 'battle':
            self.combo_owner = owner
        self.cpu_move = None
        self.miss_card = None
        self.miss_until = 0
        if owner == "you":
            self.discoveries.add((self.cards[index][0], word))
        self.used[index] = owner
        self.history.append({"word": word, "owner": owner, "icon": self.cards[index][1], "id": self.cards[index][0], "readings": self.cards[index][2], "relinked": self.break_next})
        self.break_next = False
        self.seen = {normalize_reading(w) for w in self.seen} | {normalize_reading(word)}
        self.last_word, self.required = word, tail(word)
        self.selected = self.hint = None
        self.revision += 1
        if self.required == "ん":
            self.finish("cpu" if owner == "you" else "you", "「ん」で終わったので負け！別の読み方にも注目しよう。")
            return
        self.message = f"{'リン' if owner == 'you' else 'ルナ'}：{word} → 次は「{self.required}」"
        self.refilled = None
        if self.stock:
            self.cards[index] = self.stock.pop(0)
            del self.used[index]
            # Shared rescue rule: do not end a match with a connector stranded
            # in stock. Exchange only the newly dealt card, not existing cards.
            if not self.moves():
                for j, card in enumerate(self.stock):
                    if chain_moves((card,), self.required, self.seen):
                        self.cards[index], self.stock[j] = card, self.cards[index]
                        break
            self.refilled = index
            self.message += " · 同じ場所に新しい絵！"
        if not self.stock and len(self.used) == len(self.cards):
            # A completed legal play, regardless of the certified opening route.
            self.perfect = len(self.history) == self.total
            self.finish(self.winner_by_captures(), "すべての絵をつないだ！取得枚数で勝敗を判定。")
        elif not self.moves():
            if self.mode == "solo":
                self.check_solo_blocked()
            else:
                self.finish(self.winner_by_captures(), "つながる絵がなくなった！取得枚数で勝敗を判定。")
        else:
            if self.mode == 'battle' and owner == 'cpu':
                if self.counter_active and self.difficulty == 'hard' and self.chain.players['cpu']['count'] == 7:
                    # Give the existing CPU-owned FEVER animation one visible
                    # beat before the seventh answer ends this CPU turn.
                    self.cpu_fever_hold = True
                    self.cpu_due = self.clock() + self.CPU_FEVER_HOLD
                    self.message = 'ルナがRUSH FEVER!'
                elif self.cpu_should_continue_combo():
                    self.cpu_due = self.clock() + self.cpu_delay()
                    self.prepare_cpu()
                else:
                    self.handoff()

        self.chain.sync(self.clock(), (self.turn,) if self.phase == 'playing' else ())

    def check_solo_blocked(self):
        if self.relinks and any(tail(w) != "ん" and normalize_reading(w) not in self.seen
                                for i, c in enumerate(self.cards) if i not in self.used for w in c[2]):
            self.phase = "blocked"
            self.message = "つながる絵がないよ。「つなぎ直す」で別の文字から続けよう。"
        else:
            self.finish("draw", "ここまでつながった！次は別の読み方にも挑戦しよう。")

    def command(self, action, value=None):
        self.update()  # Expired timers cannot be bypassed by late commands.
        if action == "setup" and self.phase in ("paused", "finished"):
            self.phase = "intro"
            self.selected = None
            self.counter_ready = self.counter_active = False
            self.cpu_fever_hold = False
        elif action == "mode" and self.phase == "intro" and isinstance(value, str) and value in ("battle", "solo"):
            self.mode = value
            self.counter_ready = self.counter_active = False
        elif action == "total" and self.phase == "intro" and type(value) is int and value in (12, 24, 36, 48):
            self.total = value
        elif action == "difficulty" and self.phase == "intro" and isinstance(value, str) and value in ("easy", "normal", "hard"):
            self.difficulty = value
            self.limit = {"easy": 30, "normal": 20, "hard": 12}[value]
        elif action == 'rival_style' and self.phase == 'intro' and isinstance(value, str) and value in self.RIVAL_STYLE_LABELS:
            self.rival_style = value
            self.counter_ready = self.counter_active = False
        elif action == "start" and self.phase in ("intro", "finished"):
            self.start()
        elif action == "pause" and self.phase in ("playing", "blocked"):
            self.saved_remaining = self.remaining()
            self.saved_cpu_remaining = max(0, self.cpu_due - self.clock()) if self.turn == 'cpu' else 0
            self.resume_phase = self.phase
            self.phase = "paused"
            self.chain.sync(self.clock(), ())
            self.selected = None
        elif action == "resume" and self.phase == "paused":
            self.deadline = self.clock() + self.saved_remaining
            if self.turn == 'cpu':
                self.cpu_due = self.clock() + self.saved_cpu_remaining
            self.phase = self.resume_phase
            self.chain.sync(self.clock(), (self.turn,) if self.phase == 'playing' else ())
        elif action == "restart" and self.phase == "paused":
            self.start()
        elif action == "relink" and self.phase == "blocked" and self.mode == "solo" and self.relinks:
            relink = self.best_relink()
            if relink is not None:
                initial, move = relink
                self.chain.miss('you')
                self.chain.sync(self.clock(), ('you',))
                self.relinks -= 1
                self.miss_card = None
                self.miss_until = 0
                self.required = initial
                self.last_word = "つなぎ直し"
                self.break_next = True
                self.hint = move[0]
                self.phase = "playing"
                self.message = f"「{self.required}」からもう一度つなごう！"
        elif action == "end" and self.phase == "paused" and self.mode == "solo":
            self.finish("draw", "ここまでの結果。自分のペースでまた遊ぼう！")
        elif self.phase == "playing" and self.turn == "you":
            if action == "card" and type(value) is int and 0 <= value < len(self.cards) and value not in self.used:
                # Resolve the input at its arrival time. Bounded reading
                # planning must not consume the player's combo or turn clock.
                started = self.clock()
                self.chain.sync(started, ())
                try:
                    move = self.choose_move_for_card(value)
                finally:
                    ended = self.clock()
                    self.chain.sync(ended, ('you',))
                    if self.mode == 'battle' and self.deadline > started:
                        self.deadline += max(0, ended - started)
                if move is not None:
                    self.take(*move)
                else:
                    self.chain.miss('you')
                    self.combo_owner = None
                    self.mistakes += 1
                    self.miss_card = value
                    self.miss_until = self.clock() + MISS_OUTLINE_SECONDS
                    if self.mode != "solo":
                        self.deadline -= 3
                    self.message = f"この絵は「{self.required}」につながらないよ（使用済み・ん終わりも不可）。" + (" 選び直そう。" if self.mode == "solo" else " −3秒")
                    self.revision += 1
                    self.update()
            elif action == "hint" and self.hints and self.moves():
                self.hints -= 1
                started = self.clock()
                self.chain.sync(started, ())
                move, plan = self.chain_advice()
                self.chain.sync(self.clock(), (self.turn,))
                # Thinking for a hint must not consume the player's turn time.
                if self.mode == "battle" and self.deadline > started:
                    self.deadline += max(0, self.clock() - started)
                self.hint = move[0]
                self.message = ("完走につながるルートを発見！光る絵をつなごう。" if plan['perfect']
                                else "長くつながる候補を探したよ。光る絵をつなごう。")

    def active_miss_card(self):
        """Wrong-card outline while playing/blocked and within the durable TTL."""
        if self.miss_card is None or self.clock() >= self.miss_until:
            return None
        if self.phase not in ("playing", "blocked"):
            return None
        return self.miss_card

    def snapshot(self):
        visible = self.phase in ("playing", "blocked", "finished")
        self.chain.sync(self.clock(), (self.turn,) if self.phase == 'playing' else ())
        combo_active = self.combo_owner is not None and self.phase in ('playing', 'paused') and self.combo_remaining() > 0
        you_count, cpu_count = self.capture_counts()
        return {"phase": self.phase, "turn": self.turn, "required": self.required,
                "chain": self.chain.snapshot(self.clock(), (self.turn,) if self.phase == "playing" else ()),
                "combo_active": combo_active, "combo_owner": self.combo_owner if combo_active else None,
                "combo_remaining": round(self.combo_remaining(), 1) if combo_active else 0,
                "turn_remaining": round(self.remaining(), 1) if self.phase in ('playing', 'paused') else 0,
                "cpu_target": self.cpu_move[0] if self.cpu_move is not None and self.phase == "playing" and self.turn == "cpu" and self.mode == "battle" else None,
                "cpu_progress": max(0, min(1, 1-max(0, self.cpu_due-self.clock())/self.cpu_delay())) if self.phase == "playing" and self.turn == "cpu" and self.mode == "battle" else 0,
                "last_word": self.last_word, "remaining": round(self.remaining(), 1) if self.phase in ("playing", "paused") else 0,
                "limit": self.limit, "difficulty": self.difficulty,
                "rival_style": self.rival_style, "rival_style_label": self.RIVAL_STYLE_LABELS[self.rival_style],
                "counter_ready": self.counter_ready if self.mode == 'battle' else False,
                "counter_active": self.counter_active if self.mode == 'battle' else False,
                "counter_event": self.counter_event if self.mode == 'battle' else 0,
                "effective_cpu_delay": self.cpu_delay() if self.mode == 'battle' else 0,
                "message": self.message, "winner": self.winner,
                "perfect": self.perfect and self.phase == "finished",
                "perfect_clear": self.perfect and self.phase == "finished",
                "you_count": you_count, "cpu_count": cpu_count,
                "mistakes": self.mistakes, "miss_card": self.active_miss_card(),
                "hints": self.hints, "hint": self.hint,
                "selected": self.selected, "revision": self.revision,
                "mode": self.mode, "total": self.total, "stock": len(self.stock), "completed": len(self.history),
                "relinks": self.relinks, "refilled": self.refilled, "seen": sorted(self.seen) if visible else [],
                "cards": [{"id": c[0], "icon": c[1], "words": c[2], "owner": self.used.get(i)} for i, c in enumerate(self.cards)] if visible else [],
                "catalog": [{"id": c[0], "icon": c[1], "words": c[2]} for c in CARDS] if self.phase in ("intro", "finished") else [],
                "discoveries": [{"id": i, "word": w, "owner": "you"} for i, w in sorted(self.discoveries)],
                "history": self.history if visible else []}
