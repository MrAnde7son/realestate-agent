'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/Badge';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '@/components/ui/table';
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogTrigger 
} from '@/components/ui/dialog';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from '@/components/ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { 
  Users, 
  Plus, 
  Search, 
  MoreHorizontal,
  Edit,
  UserCheck,
  UserX,
  Key,
  Trash2,
  Download,
  RefreshCw,
  X
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { PageLoader } from '@/components/ui/page-loader';
import { api } from '@/lib/api-client';
import { UserForm } from './UserForm';
import { UserFilters } from './UserFilters';

interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  phone: string;
  company: string;
  role: string;
  is_active: boolean;
  is_active_display: string;
  is_verified: boolean;
  is_demo: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  created_at: string;
  created_at_display: string;
  updated_at: string;
  last_login: string;
  last_login_display: string;
  date_joined: string;
  language: string;
  timezone: string;
  currency: string;
  date_format: string;
  notify_email: boolean;
  notify_whatsapp: boolean;
  notify_urgent: boolean;
  notification_time: string;
}

interface UserStatistics {
  total_users: number;
  active_users: number;
  inactive_users: number;
  role_counts: Record<string, number>;
  recent_registrations: number;
  recent_logins: number;
}

const ROLE_LABELS = {
  admin: 'מנהל',
  broker: 'מתווך',
  appraiser: 'שמאי',
  investor: 'משקיע',
  viewer: 'צופה',
  private: 'פרטי'
};

const ROLE_COLORS = {
  admin: 'bg-red-100 text-red-800',
  broker: 'bg-blue-100 text-blue-800',
  appraiser: 'bg-green-100 text-green-800',
  investor: 'bg-purple-100 text-purple-800',
  viewer: 'bg-gray-100 text-gray-800',
  private: 'bg-yellow-100 text-yellow-800'
};

export default function AdminUsersClient() {
  const [users, setUsers] = useState<User[]>([]);
  const [statistics, setStatistics] = useState<UserStatistics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const { toast } = useToast();

  const loadUsers = useCallback(async () => {
    try {
      setIsLoading(true);
      
      const params = new URLSearchParams({
        page: currentPage.toString(),
        page_size: pageSize.toString(),
      });
      
      if (searchTerm) params.append('search', searchTerm);
      if (roleFilter && roleFilter !== 'all') params.append('role', roleFilter);
      if (statusFilter && statusFilter !== 'all') params.append('status', statusFilter);
      
      const response = await api.get(`/api/admin/users/?${params.toString()}`);
      
      if (response.ok) {
        setUsers(response.data.results || []);
        setTotalPages(Math.ceil((response.data.count || 0) / pageSize));
      } else {
        toast({
          title: 'שגיאה',
          description: 'לא ניתן לטעון את רשימת המשתמשים',
          variant: 'destructive',
        });
      }
    } catch (error: any) {
      console.error('Failed to load users:', error);
      toast({
        title: 'שגיאה',
        description: 'שגיאה בטעינת המשתמשים',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  }, [currentPage, pageSize, searchTerm, roleFilter, statusFilter, toast]);

  const loadStatistics = useCallback(async () => {
    try {
      const response = await api.get('/api/admin/users/statistics/');
      if (response.ok) {
        setStatistics(response.data);
      }
    } catch (error) {
      console.error('Failed to load statistics:', error);
    }
  }, []);

  useEffect(() => {
    loadUsers();
    loadStatistics();
  }, [loadUsers, loadStatistics]);

  const handleCreateUser = async (userData: any) => {
    try {
      const response = await api.post('/api/admin/users/', userData);
      if (response.ok) {
        toast({
          title: 'הצלחה',
          description: 'המשתמש נוצר בהצלחה',
        });
        setIsCreating(false);
        loadUsers();
        loadStatistics();
      } else {
        toast({
          title: 'שגיאה',
          description: response.error || 'שגיאה ביצירת המשתמש',
          variant: 'destructive',
        });
      }
    } catch (error: any) {
      toast({
        title: 'שגיאה',
        description: 'שגיאה ביצירת המשתמש',
        variant: 'destructive',
      });
    }
  };

  const handleUpdateUser = async (userData: any) => {
    if (!editingUser) return;
    
    try {
      const response = await api.patch(`/api/admin/users/${editingUser.id}/`, userData);
      if (response.ok) {
        toast({
          title: 'הצלחה',
          description: 'המשתמש עודכן בהצלחה',
        });
        setIsEditing(false);
        setEditingUser(null);
        loadUsers();
        loadStatistics();
      } else {
        toast({
          title: 'שגיאה',
          description: response.error || 'שגיאה בעדכון המשתמש',
          variant: 'destructive',
        });
      }
    } catch (error: any) {
      toast({
        title: 'שגיאה',
        description: 'שגיאה בעדכון המשתמש',
        variant: 'destructive',
      });
    }
  };

  const handleToggleUserStatus = async (user: User) => {
    try {
      const action = user.is_active ? 'deactivate' : 'activate';
      const response = await api.post(`/api/admin/users/${user.id}/${action}/`);
      
      if (response.ok) {
        toast({
          title: 'הצלחה',
          description: `המשתמש ${user.is_active ? 'הושבת' : 'הופעל'} בהצלחה`,
        });
        loadUsers();
        loadStatistics();
      } else {
        toast({
          title: 'שגיאה',
          description: 'שגיאה בשינוי סטטוס המשתמש',
          variant: 'destructive',
        });
      }
    } catch (error: any) {
      toast({
        title: 'שגיאה',
        description: 'שגיאה בשינוי סטטוס המשתמש',
        variant: 'destructive',
      });
    }
  };

  const handleResetPassword = async (user: User) => {
    try {
      const response = await api.post(`/api/admin/users/${user.id}/reset_password/`);
      if (response.ok) {
        toast({
          title: 'הצלחה',
          description: `סיסמה אופסה בהצלחה. הסיסמה החדשה: ${response.data.new_password}`,
        });
      } else {
        toast({
          title: 'שגיאה',
          description: 'שגיאה באיפוס הסיסמה',
          variant: 'destructive',
        });
      }
    } catch (error: any) {
      toast({
        title: 'שגיאה',
        description: 'שגיאה באיפוס הסיסמה',
        variant: 'destructive',
      });
    }
  };

  const handleDeleteUser = async (user: User) => {
    if (!confirm(`האם אתה בטוח שברצונך למחוק את המשתמש ${user.full_name}?`)) {
      return;
    }
    
    try {
      const response = await api.delete(`/api/admin/users/${user.id}/`);
      if (response.ok) {
        toast({
          title: 'הצלחה',
          description: 'המשתמש נמחק בהצלחה',
        });
        loadUsers();
        loadStatistics();
      } else {
        toast({
          title: 'שגיאה',
          description: 'שגיאה במחיקת המשתמש',
          variant: 'destructive',
        });
      }
    } catch (error: any) {
      toast({
        title: 'שגיאה',
        description: 'שגיאה במחיקת המשתמש',
        variant: 'destructive',
      });
    }
  };

  const handleSearch = (value: string) => {
    setSearchTerm(value);
    setCurrentPage(1);
  };

  const handleRoleFilter = (value: string) => {
    setRoleFilter(value);
    setCurrentPage(1);
  };

  const handleStatusFilter = (value: string) => {
    setStatusFilter(value);
    setCurrentPage(1);
  };

  const clearFilters = () => {
    setSearchTerm('');
    setRoleFilter('all');
    setStatusFilter('all');
    setCurrentPage(1);
  };

  if (isLoading && users.length === 0) {
    return <PageLoader />;
  }

  return (
    <div className="space-y-6">
      {/* Statistics Cards */}
      {statistics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">סה&quot;כ משתמשים</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{statistics.total_users}</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">משתמשים פעילים</CardTitle>
              <UserCheck className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{statistics.active_users}</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">הרשמות אחרונות</CardTitle>
              <Plus className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{statistics.recent_registrations}</div>
              <p className="text-xs text-muted-foreground">30 יום אחרונים</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">כניסות אחרונות</CardTitle>
              <RefreshCw className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{statistics.recent_logins}</div>
              <p className="text-xs text-muted-foreground">7 ימים אחרונים</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters and Actions */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="flex items-center gap-2">
              <UserFilters
                roleFilter={roleFilter}
                statusFilter={statusFilter}
                onRoleFilter={handleRoleFilter}
                onStatusFilter={handleStatusFilter}
                onClearFilters={clearFilters}
              />
              {(searchTerm || (roleFilter && roleFilter !== 'all') || (statusFilter && statusFilter !== 'all')) && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearFilters}
                >
                  <X className="h-4 w-4 mr-2" />
                  נקה מסננים
                </Button>
              )}
            </div>
            
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={loadUsers}
                disabled={isLoading}
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                רענן
              </Button>
              
              <Dialog open={isCreating} onOpenChange={setIsCreating}>
                <DialogTrigger asChild>
                  <Button size="sm">
                    <Plus className="h-4 w-4 mr-2" />
                    הוסף משתמש
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-2xl">
                  <DialogHeader>
                    <DialogTitle>הוסף משתמש חדש</DialogTitle>
                  </DialogHeader>
                  <UserForm
                    onSubmit={handleCreateUser}
                    onCancel={() => setIsCreating(false)}
                  />
                </DialogContent>
              </Dialog>
            </div>
          </div>
          
          {/* Search Bar */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <Input
              placeholder="חפש לפי שם, אימייל או טלפון..."
              value={searchTerm}
              onChange={(e) => handleSearch(e.target.value)}
              className="pl-10"
            />
          </div>
          
        </CardHeader>
        
        <CardContent>
          {/* Users Table */}
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>שם מלא</TableHead>
                  <TableHead>אימייל</TableHead>
                  <TableHead>תפקיד</TableHead>
                  <TableHead>סטטוס</TableHead>
                  <TableHead>תאריך יצירה</TableHead>
                  <TableHead>כניסה אחרונה</TableHead>
                  <TableHead className="text-right">פעולות</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell className="font-medium">
                      <div>
                        <div className="font-semibold">{user.full_name}</div>
                        <div className="text-sm text-muted-foreground">
                          @{user.username}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>{user.email}</TableCell>
                    <TableCell>
                      <Badge className={ROLE_COLORS[user.role as keyof typeof ROLE_COLORS]}>
                        {ROLE_LABELS[user.role as keyof typeof ROLE_LABELS]}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={user.is_active ? 'default' : 'secondary'}>
                        {user.is_active_display}
                      </Badge>
                    </TableCell>
                    <TableCell>{user.created_at_display}</TableCell>
                    <TableCell>{user.last_login_display}</TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem
                            onClick={() => {
                              setEditingUser(user);
                              setIsEditing(true);
                            }}
                          >
                            <Edit className="h-4 w-4 mr-2" />
                            ערוך
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => handleToggleUserStatus(user)}
                          >
                            {user.is_active ? (
                              <>
                                <UserX className="h-4 w-4 mr-2" />
                                השבת
                              </>
                            ) : (
                              <>
                                <UserCheck className="h-4 w-4 mr-2" />
                                הפעל
                              </>
                            )}
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => handleResetPassword(user)}
                          >
                            <Key className="h-4 w-4 mr-2" />
                            אפס סיסמה
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => handleDeleteUser(user)}
                            className="text-red-600"
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            מחק
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          
          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <div className="text-sm text-muted-foreground">
                עמוד {currentPage} מתוך {totalPages}
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                >
                  הקודם
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                  disabled={currentPage === totalPages}
                >
                  הבא
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Edit User Dialog */}
      <Dialog open={isEditing} onOpenChange={setIsEditing}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>ערוך משתמש</DialogTitle>
          </DialogHeader>
          {editingUser && (
            <UserForm
              user={editingUser}
              onSubmit={handleUpdateUser}
              onCancel={() => {
                setIsEditing(false);
                setEditingUser(null);
              }}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
