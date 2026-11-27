interface MockOptions {
  method?: string,
  headers?: {},
  body?: Record<string, any> | string | FormData,
  removePreferHeader?: boolean
}

interface MockRecord {
  [key: string]: any
}

const now = () => new Date().toISOString()

const users: MockRecord[] = [
  {
    id: 1,
    username: 'operator',
    email: 'operator@mgts.ru',
    phone: '+7 495 000-00-01',
    role: 'operator',
    created_at: '2026-11-16T09:00:00Z',
    updated_at: '2026-11-16T09:00:00Z'
  },
  {
    id: 2,
    username: 'engineer',
    email: 'engineer@mgts.ru',
    phone: '+7 495 000-00-02',
    role: 'engineer',
    created_at: '2026-11-16T09:10:00Z',
    updated_at: '2026-11-16T09:10:00Z'
  },
  {
    id: 3,
    username: 'admin',
    email: 'admin@mgts.ru',
    phone: '+7 495 000-00-03',
    role: 'admin',
    created_at: '2026-11-15T08:00:00Z',
    updated_at: '2026-11-15T08:00:00Z'
  }
]

const statuses: MockRecord[] = [
  {
    id: 1,
    type: 'ok',
    description: 'Объект в нормативном состоянии'
  },
  {
    id: 2,
    type: 'check_required',
    description: 'Требуется проверка'
  },
  {
    id: 3,
    type: 'repair_required',
    description: 'Требуется ремонт'
  }
]

const infrastructureObjects: MockRecord[] = [
  {
    id: 1,
    type: 'cable_manhole',
    external_id: 'МГТС-КЛ-0001',
    place: 'Москва, ул. Хамовнический Вал, 5',
    lat: 55.7279,
    lon: 37.5686,
    status_id: 2
  },
  {
    id: 2,
    type: 'support',
    external_id: 'МГТС-ОП-0142',
    place: 'Москва, Комсомольский просп., 28',
    lat: 55.7274,
    lon: 37.5831,
    status_id: 1
  },
  {
    id: 3,
    type: 'cable_manhole',
    external_id: 'МГТС-КЛ-0007',
    place: 'Москва, ул. Льва Толстого, 14',
    lat: 55.7338,
    lon: 37.5882,
    status_id: 3
  },
  {
    id: 4,
    type: 'cabinet',
    external_id: 'МГТС-ШК-0031',
    place: 'Москва, Фрунзенская наб., 12',
    lat: 55.7271,
    lon: 37.5934,
    status_id: 1
  },
  {
    id: 5,
    type: 'support',
    external_id: 'МГТС-ОП-0157',
    place: 'Москва, ул. Усачёва, 11',
    lat: 55.7297,
    lon: 37.5672,
    status_id: 2
  }
]

const findings: MockRecord[] = [
  {
    id: 9001,
    finding_id: 9001,
    detection_id: 501,
    defect_type: 'cover_displaced',
    defect_confidence: 0.84,
    severity: 'high',
    recommended_action: 'check',
    created_at: '2026-11-17T09:31:00Z'
  },
  {
    id: 9002,
    finding_id: 9002,
    detection_id: 502,
    defect_type: 'support_tilted',
    defect_confidence: 0.71,
    severity: 'medium',
    recommended_action: 'check',
    created_at: '2026-11-17T09:31:10Z'
  },
  {
    id: 9003,
    finding_id: 9003,
    detection_id: 503,
    defect_type: 'cover_missing',
    defect_confidence: 0.88,
    severity: 'high',
    recommended_action: 'repair',
    created_at: '2026-11-17T09:31:20Z'
  },
  {
    id: 9004,
    finding_id: 9004,
    detection_id: 504,
    defect_type: 'cabinet_door_open',
    defect_confidence: 0.62,
    severity: 'medium',
    recommended_action: 'check',
    created_at: '2026-11-17T10:07:00Z'
  },
  {
    id: 9005,
    finding_id: 9005,
    detection_id: 505,
    defect_type: 'support_tilted',
    defect_confidence: 0.55,
    severity: 'low',
    recommended_action: 'check',
    created_at: '2026-11-17T10:07:20Z'
  },
  {
    id: 9006,
    finding_id: 9006,
    detection_id: 506,
    defect_type: 'cover_displaced',
    defect_confidence: 0.49,
    severity: null,
    recommended_action: 'check',
    created_at: '2026-11-17T10:41:00Z'
  }
]

const collections: Record<string, MockRecord[]> = {
  '/api/users': users,
  '/api/statuses': statuses,
  '/api/infrastructure-objects': infrastructureObjects,
  '/api/defects': findings
}

// Заглушка картинки для мок-режима, чтобы превью и миниатюры были видны.
const mockPhoto = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(
  '<svg xmlns="http://www.w3.org/2000/svg" width="320" height="240" viewBox="0 0 320 240">' +
  '<rect width="320" height="240" fill="#EEF2F7"/>' +
  '<path d="M110 95h25l10-14h30l10 14h25v60h-100z" fill="#B8C7D9"/>' +
  '<circle cx="160" cy="125" r="19" fill="#EEF2F7"/>' +
  '<text x="160" y="190" font-family="Arial, sans-serif" font-size="14" fill="#7A8CA3" text-anchor="middle">Фото (мок)</text>' +
  '</svg>'
)

function ok(data: any) {
  return {
    success: true,
    data,
    error: undefined
  }
}

function fail(title: string, description = '') {
  return {
    success: false,
    data: undefined,
    error: {
      code: -1,
      title,
      description,
      message: description
    }
  }
}

function parseBody(body: any): MockRecord {
  if (typeof body === 'string') {
    try {
      return JSON.parse(body)
    }
    catch (e) {
      return {}
    }
  }
  // FormData в моках не разбираем — она нужна только для эндпоинта фото.
  if (typeof FormData !== 'undefined' && body instanceof FormData) {
    return {}
  }
  return body || {}
}

function nextId(rows: MockRecord[]) {
  return rows.reduce((max, row) => Math.max(max, Number(row.id) || 0), 0) + 1
}

export async function mockRequest(url: string, options: MockOptions = {}) {
  const [rawPath] = url.split('?')
  const path = rawPath.replace(/\/+$/, '')
  const method = (options.method || 'GET').toUpperCase()
  const body = parseBody(options.body)

  const segments = path.split('/').filter(Boolean)
  const collectionPath = `/${segments.slice(0, 2).join('/')}`
  const rowId = segments[2]
  const rows = collections[collectionPath]

  if (!rows) {
    return fail('Мок-эндпоинт не найден', `Для ${path} не описан мок.`)
  }

  // Фото объекта: POST/DELETE /api/infrastructure-objects/{id}/photo
  if (collectionPath === '/api/infrastructure-objects' && rowId && segments[3] === 'photo') {
    const row = rows.find(item => String(item.id) === String(rowId))

    if (!row) {
      return fail('Объект не найден')
    }

    if (method === 'POST') {
      row.img_url = mockPhoto
      row.processed_img_url = mockPhoto
      row.processing_status = 'pending'
      return ok({ ...row })
    }

    if (method === 'DELETE') {
      row.img_url = null
      row.processed_img_url = null
      return ok({ ...row })
    }

    return fail('Метод не поддерживается', `${method} ${path}`)
  }

  if (method === 'GET' && !rowId) {
    return ok([...rows])
  }

  if (method === 'GET' && rowId) {
    const row = rows.find(item => String(item.id) === String(rowId))
    return row ? ok({ ...row }) : fail('Запись не найдена')
  }

  if (method === 'POST') {
    const created = {
      ...body,
      id: body.id ?? nextId(rows),
      created_at: body.created_at || now(),
      updated_at: now()
    }
    rows.push(created)
    return ok({ ...created })
  }

  if (method === 'PUT' && rowId) {
    const index = rows.findIndex(item => String(item.id) === String(rowId))

    if (index === -1) {
      return fail('Запись не найдена')
    }

    rows[index] = {
      ...rows[index],
      ...body,
      id: rows[index].id,
      updated_at: now()
    }

    return ok({ ...rows[index] })
  }

  if (method === 'DELETE' && rowId) {
    const index = rows.findIndex(item => String(item.id) === String(rowId))

    if (index === -1) {
      return fail('Запись не найдена')
    }

    rows.splice(index, 1)
    return ok(true)
  }

  return fail('Метод не поддерживается', `${method} ${path}`)
}
