// Truy vấn dữ liệu cấu trúc giải phẫu.
//
// Bảng dữ liệu anatomy.json được tạo bởi assets_source/build_labels.py, bao phủ
// toàn bộ 1347 cấu trúc trong mô hình, mỗi mục gồm: tên tiếng Việt zh / tên
// tiếng Anh en / tên Latin la / hệ thống thuộc về sys / giới thiệu intro /
// chức năng func / số mục Wikidata wd.
//
// Cạm bẫy khớp tên: GLTFLoader của three.js dùng PropertyBinding.sanitizeNodeName()
// xử lý tên nút — khoảng trắng thành gạch dưới, và xóa các ký tự dành riêng
// [ ] . : / . Vì vậy trong file GLB
//
//     "Pectoral fascia.l.001"   →   lúc chạy "Pectoral_fascial001"
//     "Vertebra T7.001"         →   lúc chạy "Vertebra_T7001"
//
// Dấu chấm bị nuốt mất, hậu tố bên và số dính vào cuối từ, không thể dùng regex
// cắt tin cậy: Vertebra_T7001 nếu tham lam lột số cuối sẽ ra "Vertebra_T", mất
// luôn số 7. Vì vậy cách làm ở đây là thử từng cách cắt ứng viên vào từ điển.
//
// Một số tên có nhiều cách cắt đều trúng từ điển (vertebra_t1001 vừa cắt được
// t1+001 vừa t10+01), chỉ nhìn chuỗi không thể phán đoán. Những tên này được
// build_labels.py xuất ra mesh-overrides.json lúc build dựa trên tên gốc chưa
// sanitize, lúc chạy ưu tiên tra nó, không đoán mò.
import DATA from './anatomy.json'
import OVERRIDES from './mesh-overrides.json'

export const LABELS = DATA

// Hậu tố chữ cái bên/nhóm: .l trái .r phải, còn lại là dấu nhóm của Blender
const SIDE_LETTERS = 'lrjmsg'

// Theo quy tắc của three.js biến đổi khóa từ điển thành dạng lúc chạy, lập chỉ mục
// tra ngược. Trong mô hình nguồn một số tên cấu trúc có khoảng trắng đầu hoặc
// khoảng trắng kép (ví dụ "Orbital part of  inferior frontal gyrus"), script
// build đã gộp khoảng trắng, còn sanitize chuyển từng khoảng trắng thành gạch
// dưới nên thừa một gạch dưới — vì vậy cả hai bên đều gộp gạch dưới liên tiếp
// thành một và bỏ đầu cuối — tên thật không có gạch dưới kép.
function sanitize(s) {
  return s
    .replace(/\s/g, '_')
    .replace(/[[\].:/]/g, '')
    .replace(/_+/g, '_')
    .replace(/^_+|_+$/g, '')
}

const BY_SANITIZED = new Map()
for (const key of Object.keys(LABELS)) {
  BY_SANITIZED.set(sanitize(key), key)
}

function clean(name) {
  return sanitize(String(name).replace(/[*]/g, '').trim().toLowerCase())
}

// Trả về { key, side } hoặc null. side là chữ cái hậu tố gốc, '' nghĩa là không có.
function resolve(s) {
  if (BY_SANITIZED.has(s)) return { key: BY_SANITIZED.get(s), side: '' }

  const digits = (s.match(/\d+$/) || [''])[0]

  // Lần lượt thử lột 1..n chữ số cuối (tương ứng .001 / .0001 ...),
  // mỗi lần lại thử xem còn một chữ cái bên không. Trúng từ điển thì coi cắt đúng.
  for (let n = digits.length; n >= 1; n--) {
    const cut = s.slice(0, s.length - n)
    if (BY_SANITIZED.has(cut)) return { key: BY_SANITIZED.get(cut), side: '' }

    const last = cut.slice(-1)
    if (SIDE_LETTERS.includes(last)) {
      const cut2 = cut.slice(0, -1)
      if (BY_SANITIZED.has(cut2)) return { key: BY_SANITIZED.get(cut2), side: last }
    }
  }

  // Trường hợp không có số, chỉ có chữ cái bên, ví dụ "Femur.l" → "Femurl"
  const tail = s.slice(-1)
  if (SIDE_LETTERS.includes(tail)) {
    const head = s.slice(0, -1)
    if (BY_SANITIZED.has(head)) return { key: BY_SANITIZED.get(head), side: tail }
  }

  return null
}

function lookupKey(rawName) {
  let s = clean(rawName)

  // Bảng nhập nhằng xuất lúc build được ưu tiên, tránh cắt nhầm lúc chạy
  const fixed = OVERRIDES[s]
  if (fixed) return { key: fixed[0], side: fixed[1] }

  const direct = resolve(s)
  if (direct) return direct

  // GLTFLoader với nút trùng tên sẽ thêm "_1"、"_2"（createUniqueName）, lột rồi thử lại
  const dedup = s.match(/^(.*)_\d+$/)
  if (dedup) {
    const retry = resolve(dedup[1])
    if (retry) return retry
  }

  // Dự phòng: lỡ nhận được tên gốc chưa sanitize ("Femur.l.001")
  let raw = s
  for (let i = 0; i < 4; i++) {
    const before = raw
    raw = raw.replace(/\.\d+$/, '').replace(/\.([lrjmsg])$/, '')
    if (raw === before) break
  }
  if (LABELS[raw]) {
    const m = s.match(/\.([lr])(?:\.\d+)?$/)
    return { key: raw, side: m ? m[1] : '' }
  }

  return null
}

// Dùng cho script build và test kiểm tra độ phủ
export function resolveName(rawName) {
  const hit = lookupKey(rawName)
  return hit ? hit.key : null
}

const SIDE_ZH = { l: '（trái）', r: '（phải）' }

// Khi chưa có trong từ điển ít nhất đưa ra tên tiếng Anh đọc được: khôi phục
// gạch dưới, bỏ hậu tố dính ở cuối từ
function fallbackName(rawName) {
  return String(rawName)
    .replace(/_\d+$/, '')
    .replace(new RegExp(`[${SIDE_LETTERS}]?\\d+$`), '')
    .replace(/_/g, ' ')
    .trim()
}

export function lookup(rawName) {
  if (!rawName) return null

  const hit = lookupKey(rawName)
  if (!hit) {
    return {
      zh: null, en: fallbackName(rawName), la: null,
      sys: null, intro: null, func: null, wd: null, side: '',
    }
  }

  const e = LABELS[hit.key]
  const sd = SIDE_ZH[hit.side] || ''
  return {
    zh: e.zh ? e.zh + sd : null,
    en: e.en,
    la: e.la || null,
    sys: e.sys || null,
    intro: e.intro || null,
    func: e.func || null,
    wd: e.wd || null,
    side: sd,
  }
}