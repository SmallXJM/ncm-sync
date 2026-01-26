export const formatTime = (isoString: string | null) => {
  if (!isoString) return '--/-- --:-- --'
  const date = new Date(isoString)
  if (isNaN(date.getTime())) return isoString

  const month = (date.getMonth() + 1).toString().padStart(2, '0')
  const day = date.getDate().toString().padStart(2, '0')

  const hours = date.getHours()
  const minutes = date.getMinutes().toString().padStart(2, '0')
  const seconds = date.getSeconds().toString().padStart(2, '0')
  const ampm = hours >= 12 ? 'PM' : 'AM'

  // hours = hours % 12
  // hours = hours ? hours : 12 // the hour '0' should be '12'
  const hoursStr = hours.toString().padStart(2, '0')

  return `${month}/${day} ${hoursStr}:${minutes}:${seconds} ${ampm}`
}