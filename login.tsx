'use client'

import { useState } from 'react'
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { GripVertical } from 'lucide-react'

interface ListItem {
  id: number
  number: string
  description: string
}

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [draggedItem, setDraggedItem] = useState<number | null>(null)
  
  // 백엔드 DB에서 받아온 데이터라고 가정
  const [items, setItems] = useState<ListItem[]>([
    { id: 1, number: "001", description: "시스템 관리자 권한" },
    { id: 2, number: "002", description: "사용자 데이터 접근" },
    { id: 3, number: "003", description: "보고서 생성 권한" },
    { id: 4, number: "004", description: "설정 변경 권한" },
    { id: 5, number: "005", description: "백업 관리 권한" },
    { id: 6, number: "006", description: "로그 조회 권한" },
    { id: 7, number: "007", description: "사용자 관리 권한" },
    { id: 8, number: "008", description: "데이터베이스 접근" }
  ])

  const handleDragStart = (e: React.DragEvent, itemId: number) => {
    setDraggedItem(itemId)
    e.dataTransfer.effectAllowed = 'move'
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }

  const handleDrop = (e: React.DragEvent, targetId: number) => {
    e.preventDefault()
    
    if (draggedItem === null || draggedItem === targetId) return

    const draggedIndex = items.findIndex(item => item.id === draggedItem)
    const targetIndex = items.findIndex(item => item.id === targetId)
    
    if (draggedIndex === -1 || targetIndex === -1) return

    const newItems = [...items]
    const [draggedItemData] = newItems.splice(draggedIndex, 1)
    newItems.splice(targetIndex, 0, draggedItemData)
    
    setItems(newItems)
    setDraggedItem(null)
  }

  const handleDragEnd = () => {
    setDraggedItem(null)
  }

  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-4">
      <div className="w-full max-w-md space-y-6">
        {/* 유저이름 입력 */}
        <Card className="bg-gray-900 border-gray-700">
          <CardContent className="p-6">
            <label htmlFor="username" className="block text-white text-sm font-medium mb-2">
              유저이름
            </label>
            <Input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="유저이름을 입력하세요"
              className="bg-gray-800 border-gray-600 text-white placeholder-gray-400 focus:border-blue-500 focus:ring-blue-500"
            />
          </CardContent>
        </Card>

        {/* 드래그 가능한 항목 리스트 */}
        <Card className="bg-gray-900 border-gray-700">
          <CardContent className="p-6">
            <h3 className="text-white text-sm font-medium mb-4">권한 목록</h3>
            <div className="space-y-2 max-h-80 overflow-y-auto">
              {items.map((item) => (
                <div
                  key={item.id}
                  draggable
                  onDragStart={(e) => handleDragStart(e, item.id)}
                  onDragOver={handleDragOver}
                  onDrop={(e) => handleDrop(e, item.id)}
                  onDragEnd={handleDragEnd}
                  className={`
                    flex items-center p-3 bg-gray-800 border border-gray-600 rounded-lg cursor-move
                    hover:bg-gray-700 transition-colors duration-200
                    ${draggedItem === item.id ? 'opacity-50' : 'opacity-100'}
                  `}
                >
                  <GripVertical className="w-4 h-4 text-gray-400 mr-3 flex-shrink-0" />
                  <div className="flex-1">
                    <span className="text-blue-400 font-mono text-sm mr-2">
                      {item.number}
                    </span>
                    <span className="text-white text-sm">
                      - {item.description}
                    </span>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 text-xs text-gray-400 text-center">
              항목을 드래그하여 순서를 변경할 수 있습니다
            </div>
          </CardContent>
        </Card>

        {/* 로그인 버튼 */}
        <button
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-lg transition-colors duration-200"
          onClick={() => {
            console.log('Username:', username)
            console.log('Items order:', items)
          }}
        >
          로그인
        </button>
      </div>
    </div>
  )
}
