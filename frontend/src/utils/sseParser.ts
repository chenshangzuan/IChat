/**
 * SSE (Server-Sent Events) 流式解析器
 *
 * 用于 fetch ReadableStream 的手动 SSE 分帧解析（EventSource 仅支持 GET）。
 * 按 SSE 规范以 \n\n 分割 event 块，解析 event: 和 data: 字段。
 */

export interface SSEEvent {
  /** 事件类型：'message'(默认) | 'tool_call' | 'approval' | 'metadata' | 'error' */
  event: string
  /** 事件数据 */
  data: string
}

export function createSSEParser(onEvent: (event: SSEEvent) => void) {
  let buffer = ''

  function processBlock(block: string) {
    let eventType = 'message'
    const dataLines: string[] = []

    const lines = block.split('\n')
    for (const line of lines) {
      if (line.startsWith('event:')) {
        eventType = line.slice(6).trim()
      } else if (line.startsWith('data:')) {
        // SSE 规范：仅移除 "data:" 后的一个前导空格
        const value = line.slice(5)
        dataLines.push(value.startsWith(' ') ? value.slice(1) : value)
      }
      // 忽略注释行（以 : 开头）和其他字段（id:, retry:）
    }

    if (dataLines.length > 0) {
      // 多个 data: 行按换行合并（SSE 规范）
      const eventData = { event: eventType, data: dataLines.join('\n') }
      console.log('[SSEParser] 触发事件:', eventData)
      onEvent(eventData)
    }
  }

  return {
    /** 喂入从 ReadableStream 读取到的文本 chunk */
    feed(chunk: string) {
      buffer += chunk

      // 按 \n\n 分割出完整的 event 块
      let sepIdx: number
      while ((sepIdx = buffer.indexOf('\n\n')) !== -1) {
        const block = buffer.slice(0, sepIdx)
        buffer = buffer.slice(sepIdx + 2)
        if (block.trim()) {
          console.log('[SSEParser] 解析块:', block)
          processBlock(block)
        }
      }
    },
  }
}
