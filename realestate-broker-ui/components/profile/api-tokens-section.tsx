'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/Badge'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Key, Plus, Trash2, Copy, Check, Eye, EyeOff, Calendar, Clock } from 'lucide-react'
import { apiClient } from '@/lib/api-client'
import { useToast } from '@/hooks/use-toast'

interface APIToken {
  id: number
  name: string
  token?: string | null
  last_used_at: string | null
  expires_at: string | null
  is_active: boolean
  is_expired: boolean
  is_valid: boolean
  created_at: string
}

export default function APITokensSection() {
  const { toast } = useToast()
  const [tokens, setTokens] = useState<APIToken[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [newTokenName, setNewTokenName] = useState('')
  const [expiresInDays, setExpiresInDays] = useState<number | ''>('')
  const [showNewTokenDialog, setShowNewTokenDialog] = useState(false)
  const [newToken, setNewToken] = useState<string | null>(null)
  const [copiedTokenId, setCopiedTokenId] = useState<number | null>(null)
  const [visibleTokens, setVisibleTokens] = useState<Set<number>>(new Set())

  useEffect(() => {
    loadTokens()
  }, [])

  const loadTokens = async () => {
    try {
      setLoading(true)
      const response = await apiClient.get<{ tokens: APIToken[] }>('/api/api-tokens')
      if (response.ok && response.data) {
        setTokens(response.data.tokens || [])
      }
    } catch (error) {
      toast({
        title: 'שגיאה',
        description: 'לא ניתן לטעון את הטוקנים',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const handleCreateToken = async () => {
    if (!newTokenName.trim()) {
      toast({
        title: 'שגיאה',
        description: 'אנא הזן שם לטוקן',
        variant: 'destructive',
      })
      return
    }

    try {
      setCreating(true)
      const response = await apiClient.post<{ token: APIToken; message: string }>('/api/api-tokens/create', {
        name: newTokenName,
        expires_in_days: expiresInDays ? Number(expiresInDays) : null,
      })

      if (response.ok && response.data) {
        setNewToken(response.data.token.token || null)
        setShowNewTokenDialog(true)
        setNewTokenName('')
        setExpiresInDays('')
        await loadTokens()
      }
    } catch (error: any) {
      toast({
        title: 'שגיאה',
        description: error.message || 'לא ניתן ליצור טוקן',
        variant: 'destructive',
      })
    } finally {
      setCreating(false)
    }
  }

  const handleDeleteToken = async (tokenId: number) => {
    if (!confirm('האם אתה בטוח שברצונך למחוק את הטוקן הזה?')) {
      return
    }

    try {
      const response = await apiClient.delete(`/api/api-tokens/${tokenId}/delete`)
      if (response.ok) {
        toast({
          title: 'הצלחה',
          description: 'הטוקן נמחק בהצלחה',
        })
        await loadTokens()
      }
    } catch (error: any) {
      toast({
        title: 'שגיאה',
        description: error.message || 'לא ניתן למחוק את הטוקן',
        variant: 'destructive',
      })
    }
  }

  const handleToggleToken = async (tokenId: number, isActive: boolean) => {
    try {
      const response = await apiClient.patch(`/api/api-tokens/${tokenId}`, {
        is_active: !isActive,
      })
      if (response.ok) {
        await loadTokens()
      }
    } catch (error: any) {
      toast({
        title: 'שגיאה',
        description: error.message || 'לא ניתן לעדכן את הטוקן',
        variant: 'destructive',
      })
    }
  }

  const copyToClipboard = (text: string, tokenId?: number) => {
    navigator.clipboard.writeText(text)
    if (tokenId) {
      setCopiedTokenId(tokenId)
      setTimeout(() => setCopiedTokenId(null), 2000)
    } else {
      toast({
        title: 'הועתק',
        description: 'הטוקן הועתק ללוח',
      })
    }
  }

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'ללא תאריך תפוגה'
    return new Date(dateString).toLocaleDateString('he-IL', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    })
  }

  const toggleTokenVisibility = (tokenId: number) => {
    const newVisible = new Set(visibleTokens)
    if (newVisible.has(tokenId)) {
      newVisible.delete(tokenId)
    } else {
      newVisible.add(tokenId)
    }
    setVisibleTokens(newVisible)
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Key className="h-5 w-5" />
              API
            </CardTitle>
            <CardDescription>
              נהל טוקני API לגישה תוכניתית ל-API.
            </CardDescription>
          </div>
          <Dialog open={showNewTokenDialog} onOpenChange={setShowNewTokenDialog}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 ms-2" />
                צור טוקן חדש
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>צור טוקן API חדש</DialogTitle>
                <DialogDescription>
                  הזן שם תיאורי לטוקן. הטוקן יוצג רק פעם אחת - שמור אותו במקום בטוח!
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="token-name">שם הטוקן</Label>
                  <Input
                    id="token-name"
                    placeholder="לדוגמה: Real Estate Agent"
                    value={newTokenName}
                    onChange={(e) => setNewTokenName(e.target.value)}
                  />
                </div>
                <div>
                  <Label htmlFor="expires-days">תוקף (ימים, ריק = ללא תפוגה)</Label>
                  <Input
                    id="expires-days"
                    type="number"
                    placeholder="30"
                    value={expiresInDays}
                    onChange={(e) => setExpiresInDays(e.target.value ? Number(e.target.value) : '')}
                  />
                </div>
                {newToken && (
                  <Alert>
                    <AlertDescription>
                      <div className="space-y-2">
                        <p className="font-semibold">טוקן נוצר בהצלחה!</p>
                        <div className="flex items-center gap-2">
                          <code className="flex-1 p-2 bg-muted rounded text-sm break-all">
                            {newToken}
                          </code>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => copyToClipboard(newToken)}
                          >
                            {copiedTokenId === -1 ? (
                              <Check className="h-4 w-4" />
                            ) : (
                              <Copy className="h-4 w-4" />
                            )}
                          </Button>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          ⚠️ שמור את הטוקן הזה במקום בטוח - הוא לא יוצג שוב!
                        </p>
                      </div>
                    </AlertDescription>
                  </Alert>
                )}
                <div className="flex gap-2">
                  <Button onClick={handleCreateToken} disabled={creating || !newTokenName.trim()}>
                    {creating ? 'יוצר...' : 'צור טוקן'}
                  </Button>
                  <Button variant="outline" onClick={() => {
                    setShowNewTokenDialog(false)
                    setNewToken(null)
                    setNewTokenName('')
                    setExpiresInDays('')
                  }}>
                    ביטול
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="text-center py-8 text-muted-foreground">טוען...</div>
        ) : tokens.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            אין טוקנים. צור טוקן חדש כדי להתחיל.
          </div>
        ) : (
          <div className="space-y-4">
            {tokens.map((token) => (
              <div
                key={token.id}
                className="border rounded-lg p-4 space-y-3"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h4 className="font-semibold">{token.name}</h4>
                      {token.is_valid ? (
                        <Badge variant="default">פעיל</Badge>
                      ) : token.is_expired ? (
                        <Badge variant="destructive">פג תוקף</Badge>
                      ) : (
                        <Badge variant="secondary">לא פעיל</Badge>
                      )}
                    </div>
                    {token.token && visibleTokens.has(token.id) && (
                      <div className="flex items-center gap-2 mb-2">
                        <code className="flex-1 p-2 bg-muted rounded text-sm break-all font-mono">
                          {token.token}
                        </code>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => copyToClipboard(token.token!, token.id)}
                        >
                          {copiedTokenId === token.id ? (
                            <Check className="h-4 w-4" />
                          ) : (
                            <Copy className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                    )}
                    <div className="space-y-1 text-sm text-muted-foreground">
                      <div className="flex items-center gap-2">
                        <Calendar className="h-4 w-4" />
                        נוצר: {formatDate(token.created_at)}
                      </div>
                      {token.expires_at && (
                        <div className="flex items-center gap-2">
                          <Clock className="h-4 w-4" />
                          תפוגה: {formatDate(token.expires_at)}
                        </div>
                      )}
                      {token.last_used_at && (
                        <div className="flex items-center gap-2">
                          <Clock className="h-4 w-4" />
                          שימוש אחרון: {formatDate(token.last_used_at)}
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {token.token && (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => toggleTokenVisibility(token.id)}
                      >
                        {visibleTokens.has(token.id) ? (
                          <EyeOff className="h-4 w-4" />
                        ) : (
                          <Eye className="h-4 w-4" />
                        )}
                      </Button>
                    )}
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleToggleToken(token.id, token.is_active)}
                    >
                      {token.is_active ? 'השבת' : 'הפעל'}
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleDeleteToken(token.id)}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

