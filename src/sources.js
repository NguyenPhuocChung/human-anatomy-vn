// Nguồn dữ liệu. Thanh bên và panel "Nguồn" render dựa trên đây, từng cấu trúc còn có liên kết Wikidata để đối chiếu trực tiếp.
export const SOURCES = [
  {
    key: 'ta2',
    label: 'Tên Latin · Tên tiếng Anh',
    name: 'Terminologia Anatomica ấn bản 2 (FIPAT/IFAA, 2019)',
    note: 'Tiêu chuẩn thuật ngữ giải phẫu quốc tế, dự án này đính kèm bảng từ TA2 trong kho (CC BY-ND 4.0).',
    url: 'https://ifaa.unifr.ch/Public/EntryPage/ViewTA2Part1.html',
  },
  {
    key: 'cnterm',
    label: 'Tên tiếng Trung',
    name: '《Thuật ngữ Giải phẫu Cơ thể Người》 ấn bản 2 · Ủy ban Thẩm định Thuật ngữ Khoa học Kỹ thuật Toàn quốc',
    note: 'Thuật ngữ giải phẫu chuẩn do nhà nước thẩm định công bố, có thể tra cứu từng mục trên "Thuật ngữ Trực tuyến".',
    url: 'https://www.termonline.cn/',
  },
  {
    key: 'pmph',
    label: 'Giới thiệu · Chức năng',
    name: '《Giải phẫu Hệ thống》 ấn bản 9, Nhà xuất bản Nhân dân Vệ sinh',
    note: 'Mô tả cấu trúc, điểm bám và chức năng chủ yếu dựa theo giáo trình này.',
    url: 'https://book.douban.com/subject/30481982/',
  },
  {
    key: 'kenhub',
    label: 'Giới thiệu · Chức năng (bổ sung)',
    name: 'Kenhub bản tiếng Trung / IMAIOS e-Anatomy bản tiếng Trung',
    note: 'Dùng để bổ sung các điểm lâm sàng và mô tả chi tiết của một số cấu trúc.',
    url: 'https://www.kenhub.cn/',
  },
  {
    key: 'wikidata',
    label: 'Đối chiếu từng mục',
    name: 'Wikidata (liên kết qua thuộc tính TA2 ID P7173)',
    note: 'Dự án này có 1112 cấu trúc kèm liên kết mục Wikidata, có thể click để đối chiếu tên đa ngôn ngữ và mã cơ sở dữ liệu bên ngoài.',
    url: 'https://www.wikidata.org/wiki/Property:P7173',
  },
  {
    key: 'zanatomy',
    label: 'Mô hình 3D',
    name: 'Z-Anatomy (nguồn từ BodyParts3D)',
    note: 'Nguồn của mô hình và tên tiếng Anh của cấu trúc, CC BY-SA 4.0.',
    url: 'https://github.com/Z-Anatomy',
  },
]