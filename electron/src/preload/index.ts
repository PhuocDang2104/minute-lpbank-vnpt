import { contextBridge } from 'electron'

// Expose minimal safe bridge for renderer
contextBridge.exposeInMainWorld('meetmate', {
  ping: () => 'pong',
})