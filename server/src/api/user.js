// 本地模式：无需远程API调用，保留接口以兼容现有代码

export function login(data) {
  return Promise.resolve({ code: 20000, data: { token: 'local-token' } })
}

export function getInfo(token) {
  return Promise.resolve({
    code: 20000,
    data: {
      roles: ['admin'],
      name: 'Local User',
      avatar: '',
      introduction: 'Local mode user'
    }
  })
}

export function logout() {
  return Promise.resolve({ code: 20000, data: 'success' })
}
