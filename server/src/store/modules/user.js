// 本地模式：简化用户状态管理，无需远程API
import router, { resetRouter } from '@/router'

const state = {
  name: 'Local User',
  avatar: '',
  introduction: 'Local mode user',
  roles: ['admin']
}

const mutations = {
  SET_INTRODUCTION: (state, introduction) => {
    state.introduction = introduction
  },
  SET_NAME: (state, name) => {
    state.name = name
  },
  SET_AVATAR: (state, avatar) => {
    state.avatar = avatar
  },
  SET_ROLES: (state, roles) => {
    state.roles = roles
  }
}

const actions = {
  // 本地模式：直接返回成功
  login({ commit }, userInfo) {
    return Promise.resolve()
  },

  // 本地模式：返回本地用户信息
  getInfo({ commit, state }) {
    return Promise.resolve({
      roles: state.roles,
      name: state.name,
      avatar: state.avatar,
      introduction: state.introduction
    })
  },

  // 本地模式：登出无需操作
  logout({ commit, state, dispatch }) {
    return Promise.resolve()
  },

  // 本地模式：重置角色
  resetToken({ commit }) {
    return Promise.resolve()
  },

  // 本地模式：动态修改权限（保留功能但简化）
  async changeRoles({ commit, dispatch }, role) {
    const roles = [role]
    commit('SET_ROLES', roles)
    resetRouter()
    dispatch('tagsView/delAllViews', null, { root: true })
  }
}

export default {
  namespaced: true,
  state,
  mutations,
  actions
}
