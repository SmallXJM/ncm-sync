import { describe, expect, it } from 'vitest'
import {
  validateCronExpr,
  validateIntRange,
  validateNcmConfigDraft,
  validatePathLike,
  validateTemplateString,
} from '@/utils/configValidation'

describe('configValidation', () => {
  describe('validateCronExpr', () => {
    it('accepts null to disable scheduler', () => {
      expect(validateCronExpr(null)).toBeNull()
    })

    it('rejects empty string', () => {
      expect(validateCronExpr('')).toBeTruthy()
      expect(validateCronExpr('   ')).toBeTruthy()
    })

    it('accepts 5-part cron', () => {
      expect(validateCronExpr('0 2 * * *')).toBeNull()
    })

    it('accepts 6-part cron', () => {
      expect(validateCronExpr('0 0 2 * * *')).toBeNull()
    })

    it('rejects invalid part count', () => {
      expect(validateCronExpr('0 2 * *')).toBeTruthy()
    })
  })

  describe('validateIntRange', () => {
    it('rejects non-number', () => {
      expect(validateIntRange('abc', { min: 1, max: 10, label: 'X' })).toBeTruthy()
    })

    it('rejects float', () => {
      expect(validateIntRange(1.1, { min: 1, max: 10, label: 'X' })).toBeTruthy()
    })

    it('rejects out of range', () => {
      expect(validateIntRange(0, { min: 1, max: 10, label: 'X' })).toBeTruthy()
      expect(validateIntRange(11, { min: 1, max: 10, label: 'X' })).toBeTruthy()
    })

    it('accepts integer in range', () => {
      expect(validateIntRange(5, { min: 1, max: 10, label: 'X' })).toBeNull()
    })
  })

  describe('validatePathLike', () => {
    it('rejects empty', () => {
      expect(validatePathLike('', '路径')).toBeTruthy()
    })

    it('rejects newline', () => {
      expect(validatePathLike('a\nb', '路径')).toBeTruthy()
    })

    it('accepts normal string', () => {
      expect(validatePathLike('downloads', '路径')).toBeNull()
    })
  })

  describe('validateTemplateString', () => {
    it('accepts balanced braces', () => {
      expect(validateTemplateString('{artist} - {title}', '模板')).toBeNull()
    })

    it('rejects extra closing brace', () => {
      expect(validateTemplateString('artist}', '模板')).toBeTruthy()
    })

    it('rejects missing closing brace', () => {
      expect(validateTemplateString('{artist - {title}', '模板')).toBeTruthy()
    })
  })

  describe('validateNcmConfigDraft', () => {
    it('returns field errors by key', () => {
      const errors = validateNcmConfigDraft({
        download: {
          cron_expr: '0 2 * *',
          max_concurrent_downloads: 0,
          max_threads_per_download: 999,
          temp_downloads_dir: '',
        },
        template: {
          filename: 'artist}',
          music_dir_prefix_playlist: '',
        },
      })

      expect(errors['download.cron_expr']).toBeTruthy()
      expect(errors['download.max_concurrent_downloads']).toBeTruthy()
      expect(errors['download.max_threads_per_download']).toBeTruthy()
      expect(errors['download.temp_downloads_dir']).toBeTruthy()
      expect(errors['template.filename']).toBeTruthy()
      expect(errors['template.music_dir_prefix_playlist']).toBeTruthy()
    })
  })
})

