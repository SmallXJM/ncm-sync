import * as user from './user'

const music = {
  user,
} as const

export type music = typeof music
export default music


