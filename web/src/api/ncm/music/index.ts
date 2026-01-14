import * as user from './user'
import * as song from './song'

const music = {
  user,
  song,
} as const

export type music = typeof music
export default music
