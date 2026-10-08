# -*- coding: utf-8 -*-
"""
Xây dựng src/anatomy.json: ánh xạ tên mesh tiếng Anh trong GLB sang
Tên tiếng Việt / Tên tiếng Anh / Tên Latin / Hệ thống thuộc về / Giới thiệu / Chức năng / Liên kết đối chiếu bên ngoài.

Nguồn dữ liệu (đồng thời hiển thị ở thanh bên trang web, xem src/sources.js và README):
  1. Tên Latin  —— assets_source/TA2.csv，FIPAT《Terminologia Anatomica》ấn bản 2 (2019)，CC BY-ND 4.0
  2. Tên tiếng Anh  —— cùng cột tiếng Anh của TA2; tên cấu trúc trong model đến từ Z-Anatomy
  3. Tên tiếng Việt  —— dựa theo Ủy ban Thẩm định Thuật ngữ Khoa học Kỹ thuật Toàn quốc《Thuật ngữ Giải phẫu Cơ thể Người》ấn bản 2 (termonline.cn)
                và Nhà xuất bản Nhân dân Vệ sinh《Giải phẫu Hệ thống》ấn bản 9, được thẩm định thủ công từng mục
  4. Giới thiệu/Chức năng —— biên soạn dựa trên《Giải phẫu Hệ thống》ấn bản 9, Kenhub bản tiếng Trung, IMAIOS e-Anatomy bản tiếng Trung
  5. Wikidata QID —— liên kết qua TA2 ID (thuộc tính P7173), để frontend cung cấp liên kết đối chiếu từng mục có thể click

Cách dùng:  python assets_source/build_labels.py
Đầu ra:  src/anatomy.json  và in tỷ lệ phủ cùng danh sách chưa phủ ra terminal
"""
import json
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, 'public', 'models')
OUT = os.path.join(ROOT, 'src', 'anatomy.json')
OUT_OVERRIDES = os.path.join(ROOT, 'src', 'mesh-overrides.json')
TA2_CSV = os.path.join(ROOT, 'assets_source', 'TA2.csv')
WD_JSON = os.path.join(ROOT, 'assets_source', 'wikidata_ta2.json')

SYSTEM_ZH = {
    'skeleton': 'Hệ xương',
    'muscular': 'Hệ cơ',
    'cardiovascular': 'Hệ tim mạch',
    'nervous': 'Hệ thần kinh và giác quan',
    'visceral': 'Hệ nội tạng',
}

CN_NUM = '一二三四五六七八九十'


def cn(i):
    """1..12 -> 一..十二"""
    if i <= 10:
        return CN_NUM[i - 1]
    return '十' + CN_NUM[i - 11]


# ---------------------------------------------------------------- Đọc GLB
def glb_json(path):
    data = open(path, 'rb').read()
    off, js = 12, None
    while off < len(data):
        clen, ctype = struct.unpack('<II', data[off:off + 8])
        if ctype == 0x4E4F534A:
            js = json.loads(data[off + 8:off + 8 + clen].decode('utf-8'))
        off += 8 + clen
    return js


def base_name(raw):
    """Bỏ số hiệu .001 của Blender và hậu tố .l/.r/.j/.g, lấy tên cấu trúc gốc."""
    s = raw.strip()
    s = re.sub(r'\.\d+$', '', s)
    s = re.sub(r'\.(l|r|j|m|s|g)$', '', s, flags=re.I)
    return re.sub(r'\s+', ' ', s).strip()


def collect_structures():
    """Trả về {tên gốc: id hệ thống}, nếu cùng tên xuất hiện ở nhiều model thì lấy hệ thống xuất hiện lần đầu."""
    out = {}
    for fn in sorted(os.listdir(MODELS)):
        if not fn.endswith('.glb'):
            continue
        js = glb_json(os.path.join(MODELS, fn))
        for node in js.get('nodes', []):
            if 'mesh' in node:
                out.setdefault(base_name(node.get('name', '')), fn[:-4])
    return out


# ---------------------------------------------------------------- Dữ liệu bên ngoài
def load_ta2():
    by_en = {}
    with open(TA2_CSV, encoding='utf-8-sig') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('"') and line.endswith('"'):
                line = line[1:-1]
            p = line.split(';')
            if len(p) < 3 or p[0] == 'TA2ID':
                continue
            by_en.setdefault(p[1].strip().lower(), (p[0], p[2].strip()))
    return by_en


def load_wikidata():
    if not os.path.exists(WD_JSON):
        return {}
    out = {}
    for r in json.load(open(WD_JSON, encoding='utf-8')):
        if r.get('ta2') and r.get('qid'):
            out.setdefault(str(r['ta2']), r['qid'])
    return out


def key_of(name):
    return re.sub(r'\s+', ' ', name.replace('*', '')).strip().lower()


# ---------------------------------------------------------------- Đăng ký mục từ
TERMS = {}


def add(table):
    """table: {Tên tiếng Anh: (Tên tiếng Việt, Giới thiệu, Chức năng)}"""
    for en, v in table.items():
        TERMS[key_of(en)] = v


# ============================ Chuỗi quy tắc ============================
ORD_EN = ['first', 'second', 'third', 'fourth', 'fifth', 'sixth',
          'seventh', 'eighth', 'ninth', 'tenth', 'eleventh', 'twelfth']


def ribs():
    t = {}
    special = {
        1: ('Xương sườn ngắn nhất, dẹt nhất, độ cong lớn nhất, tạo thành bờ trước–ngoài của cửa trên lồng ngực.',
            'Mặt trên có củ cơ bậc thang trước và rãnh động–tĩnh mạch dưới đòn, bảo vệ mạch máu và đám rối cánh tay đi qua cửa trên lồng ngực.'),
        2: ('Mảnh và dài hơn xương sườn 1, mặt ngoài có lồi củ cơ răng trước.', 'Tạo thành thành bên phần trên lồng ngực, là điểm bám của cơ răng trước, là mốc đếm ở mặt phẳng góc ức.'),
        11: ('Xương sườn tự do, đầu trước tự do không nối sụn sườn.', 'Bảo vệ phía sau thận và lách, là điểm bám của cơ thành bụng và cơ hoành.'),
        12: ('Xương sườn tự do ngắn nhất, đầu trước tự do.', 'Là điểm bám của cơ vuông thắt lưng và cơ hoành, cũng là mốc xương của điểm đau gõ vùng thận.'),
    }
    for i, w in enumerate(ORD_EN, 1):
        intro, func = special.get(i, (
            f'Xương sườn hình cung dẹt thứ {i} của lồng ngực, đầu sau khớp với đốt sống ngực, đầu trước nối sụn sườn.',
            'Tạo thành thành bên lồng ngực, bảo vệ tạng khoang ngực, và nâng–hạ khi hô hấp để thay đổi thể tích lồng ngực.'))
        t[f'{w.capitalize()} rib'] = (f'Xương sườn {cn(i)}', intro, func)
        if i <= 10:
            t[f'Costal cartilage of {w} rib'] = (
                f'Sụn sườn {cn(i)}',
                f'Sụn trong suốt nối vào đầu trước xương sườn {i} (sụn sườn 8–10 lần lượt bám vào sụn sườn trên tạo thành cung sườn).',
                'Tạo độ đàn hồi cho lồng ngực, cho phép xương sườn nâng–hạ khi hô hấp mà không bị gãy.')
    return t


def vertebrae():
    t = {}
    for i in range(3, 8):
        extra = 'Gai sống đốt sống cổ 7 dài và đầu tận không chẻ đôi, nhô dưới da, gọi là đốt sống lồi, là mốc đếm đốt sống trên bề mặt.' if i == 7 else ''
        t[f'Vertebra C{i}'] = (
            f'Đốt sống cổ {cn(i)}',
            f'Đốt sống thứ {i} đoạn cổ, thân nhỏ, gốc mỏm ngang có lỗ mỏm ngang để động mạch đốt sống đi qua.{extra}',
            'Chống đỡ đầu và bảo vệ tủy sống đoạn cổ, cho phép cổ gập–duỗi, nghiêng bên và xoay với biên độ lớn.')
    for i in range(1, 13):
        t[f'Vertebra T{i}'] = (
            f'Đốt sống ngực {cn(i)}',
            f'Đốt sống thứ {i} đoạn ngực, mặt bên thân có hố sườn khớp với đầu xương sườn {i}, gai sống dài và nghiêng xuống dưới.',
            'Cùng xương sườn và xương ức tạo thành lồng ngực bảo vệ tim phổi, cột sống đoạn ngực chủ yếu cử động xoay.')
    for i in range(1, 6):
        t[f'Vertebra L{i}'] = (
            f'Đốt sống thắt lưng {cn(i)}',
            f'Đốt sống thứ {i} đoạn thắt lưng, thân to, gai sống rộng và hướng ngang ra sau.',
            'Chịu phần lớn trọng lượng nửa trên cơ thể, cho phép thân gập trước, duỗi sau và nghiêng bên.')
    return t


DIGIT = {'first': '一', 'second': '二', 'third': '三', 'fourth': '四', 'fifth': '五'}


def phalanges():
    t = {}
    seg = {'Proximal': ('gần', 'đốt gần nhất với xương bàn tay/bàn chân'),
           'Middle': ('giữa', 'đốt nằm giữa đốt gần và đốt xa'),
           'Distal': ('xa', 'đốt tận cùng, nâng đỡ giường móng')}
    for part, (pz, pd) in seg.items():
        for hf, (hz, dz, act) in {'hand': ('tay', 'ngón', 'nắm và cử động tinh tế'),
                                  'foot': ('chân', 'ngón', 'đứng và đẩy đất')}.items():
            for d, dz_num in DIGIT.items():
                if part == 'Middle' and d == 'first':
                    continue  # ngón cái tay và ngón cái chân chỉ có đốt gần và đốt xa
                t[f'{part} phalanx of {d} finger of {hf}'] = (
                    f'Xương đốt {pz} ngón {dz_num} {dz}',
                    f'Xương đốt {pz} của ngón {dz_num} {hz}, {pd}.',
                    f'Tạo khung xương của ngón {dz} đó, là điểm bám của gân gấp và gân duỗi, tham gia {act}.')
    return t


def metacarpals():
    t = {}
    for d, n in DIGIT.items():
        t[f'{d.capitalize()} metacarpal bone'] = (
            f'Xương bàn tay {n}',
            f'Xương bàn tay thứ {n} của lòng bàn tay, đầu gần khớp với xương cổ tay, đầu xa tạo khớp bàn–ngón với xương đốt gần.',
            'Tạo khung xương lòng bàn tay và tạo cung bàn tay, truyền lực nắm từ ngón tay về cổ tay.')
        t[f'{d.capitalize()} metatarsal bone'] = (
            f'Xương bàn chân {n}',
            f'Xương bàn chân thứ {n} của bàn chân, đầu gần khớp với xương cổ chân, đầu xa tạo khớp bàn–ngón với xương đốt gần.',
            'Tạo phần trước cung bàn chân, khi đứng và đi phân tán và truyền trọng lượng về phía trước.')
    return t


def teeth():
    t = {}
    rows = {
        'medial incisor': ('răng cửa giữa', 'mặt nhai hình đục, bờ cắt sắc, một chân.', 'cắt thức ăn, đồng thời tham gia phát âm và tạo hình diện mạo.'),
        'lateral incisor': ('răng cửa bên', 'nằm ngoài răng cửa giữa, hình dạng tương tự nhưng nhỏ hơn.', 'cắt thức ăn.'),
        'canine': ('răng nanh', 'mặt nhai có một múi nhọn sắc, chân dài nhất trong miệng.', 'xé thức ăn, đồng thời nâng đỡ hình dáng góc miệng.'),
        'first premolar': ('răng hàm nhỏ thứ nhất', 'mặt nhai có hai múi má và lưỡi.', 'hỗ trợ xé và nghiền sơ bộ thức ăn.'),
        'second premolar': ('răng hàm nhỏ thứ hai', 'mặt nhai có hai múi má và lưỡi, thường một chân.', 'hỗ trợ nghiền thức ăn.'),
        'first molar tooth': ('răng hàm lớn thứ nhất', 'răng hàm lớn mọc sớm nhất, mặt nhai rộng, có 4–5 múi.', 'nghiền thức ăn, là răng then chốt thiết lập quan hệ khớp cắn.'),
        'second molar tooth': ('răng hàm lớn thứ hai', 'nằm xa răng hàm lớn thứ nhất, mặt nhai rộng.', 'nghiền thức ăn.'),
    }
    for up, upz in (('Upper', 'hàm trên'), ('Lower', 'hàm dưới')):
        for k, (zh, intro, func) in rows.items():
            t[f'{up} {k}'] = (f'{upz}{zh}', f'{zh} trong cung răng {upz}, {intro}', func)
    return t


# Các mục từ biên soạn thủ công từng điều, lưu theo hệ thống trong assets_source/terms/
from terms import skeleton, muscular, nervous, cardiovascular, visceral  # noqa: E402

EXPLICIT = [skeleton.TERMS, muscular.TERMS, nervous.TERMS,
            cardiovascular.TERMS, visceral.TERMS]


# ============================ Quy trình chính ============================
def register_all():
    add(ribs())
    add(vertebrae())
    add(phalanges())
    add(metacarpals())
    add(teeth())
    for tbl in EXPLICIT:
        add(tbl)


# ------------------------------------------------ Bảng tên runtime / bảng mơ hồ của three.js
# GLTFLoader của three.js dùng PropertyBinding.sanitizeNodeName() xử lý tên node:
# khoảng trắng đổi thành gạch dưới, và xóa [ ] . : / . Sau khi xóa dấu chấm, hậu tố bên và số hiệu sẽ dính vào cuối từ,
# ví dụ "Vertebra T1.001" và "Vertebra T10.001" lần lượt trở thành vertebra_t1001 và
# vertebra_t10001——lúc này điểm cắt không thể xác định chỉ từ chuỗi (t1+001 hay t10+001).
#
# Hầu hết tên chỉ có một cách cắt hợp lệ trúng từ điển, frontend thử lần lượt các ứng viên là đủ. Ở đây chỉ xuất
# những tên **thực sự có nhiều cách cắt hợp lệ** thành một bảng mơ hồ nhỏ giao cho frontend, tránh phải đoán.
# Việc có mơ hồ hay không do dữ liệu quyết định, model đổi thì chạy lại là được, không phụ thuộc thứ tự thử của frontend.
def runtime_name(raw):
    """Tái hiện sanitizeNodeName của three.js + chuẩn hóa clean() của frontend."""
    s = raw.replace('*', '').lower()
    s = re.sub(r'\s', '_', s)
    s = re.sub(r'[\[\].:/]', '', s)
    s = re.sub(r'_+', '_', s)
    return s.strip('_')


def sanitize_key(k):
    s = re.sub(r'\s', '_', k)
    s = re.sub(r'[\[\].:/]', '', s)
    s = re.sub(r'_+', '_', s)
    return s.strip('_')


SIDE_LETTERS = 'lrjmsg'


def candidate_keys(rt, by_sanitized):
    """Liệt kê tất cả cách cắt của rt có thể trúng từ điển, trả về [(key, side), ...]."""
    out = []
    if rt in by_sanitized:
        out.append((by_sanitized[rt], ''))
    m = re.search(r'\d+$', rt)
    digits = m.group(0) if m else ''
    for n in range(1, len(digits) + 1):
        cut = rt[:-n]
        if cut in by_sanitized:
            out.append((by_sanitized[cut], ''))
        if cut and cut[-1] in SIDE_LETTERS and cut[:-1] in by_sanitized:
            out.append((by_sanitized[cut[:-1]], cut[-1]))
    # bỏ trùng giữ thứ tự
    return list(dict.fromkeys(out))


def build_overrides(out):
    """Quét toàn bộ tên mesh, xuất bảng mơ hồ {tên runtime: [khóa từ điển, chữ cái bên]}."""
    by_sanitized = {sanitize_key(k): k for k in out}
    overrides = {}
    seen = 0
    for fn in sorted(os.listdir(MODELS)):
        if not fn.endswith('.glb'):
            continue
        js = glb_json(os.path.join(MODELS, fn))
        for node in js.get('nodes', []):
            if 'mesh' not in node:
                continue
            raw = node.get('name', '')
            seen += 1
            rt = runtime_name(raw)
            cands = candidate_keys(rt, by_sanitized)
            if len(cands) <= 1:
                continue
            # câu trả lời thật lấy từ tên gốc chưa sanitize, đáng tin
            truth_key = key_of(base_name(raw))
            m = re.search(r'\.([lr])(?:\.\d+)?$', raw)
            overrides[rt] = [truth_key, m.group(1) if m else '']
    return overrides, seen


def build():
    register_all()
    structures = collect_structures()
    ta2 = load_ta2()
    wd = load_wikidata()

    out, missing = {}, []
    for name, layer in sorted(structures.items()):
        k = key_of(name)
        hit = TERMS.get(k)
        ta = ta2.get(k)
        entry = {
            'en': name,
            'sys': SYSTEM_ZH.get(layer, layer),
        }
        if ta:
            entry['la'] = ta[1]
            qid = wd.get(ta[0])
            if qid:
                entry['wd'] = qid
        if hit:
            entry['zh'], entry['intro'], entry['func'] = hit
        else:
            missing.append((layer, name))
        out[k] = entry

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=0, sort_keys=True)

    overrides, mesh_count = build_overrides(out)
    with open(OUT_OVERRIDES, 'w', encoding='utf-8') as f:
        json.dump(overrides, f, ensure_ascii=False, indent=0, sort_keys=True)

    total = len(out)
    done = total - len(missing)
    print(f'Tổng số cấu trúc {total}  Đã có tiếng Việt {done} ({done*100//total}%)  Còn thiếu {len(missing)}')
    print(f'Phủ tên Latin {sum(1 for v in out.values() if v.get("la"))}')
    print(f'Liên kết Wikidata {sum(1 for v in out.values() if v.get("wd"))}')
    print(f'Tổng số mesh {mesh_count}  Tên runtime mơ hồ {len(overrides)} mục đã ghi vào bảng mơ hồ')
    for rt, (k, s) in sorted(overrides.items()):
        print(f'    {rt} -> {k}{("." + s) if s else ""}')
    by_layer = {}
    for layer, n in missing:
        by_layer.setdefault(layer, []).append(n)
    for layer in sorted(by_layer):
        print(f'\n--- Còn thiếu {layer} ({len(by_layer[layer])}) ---')
        for n in by_layer[layer]:
            print(' ', n)
    return out


if __name__ == '__main__':
    build()