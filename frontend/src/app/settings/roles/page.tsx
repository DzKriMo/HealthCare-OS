"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { api } from "@/lib/api/client";
import type { Role, Permission } from "@healthcare-os/types";

export default function RolesPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, fetchCurrentUser, logout } =
    useAuthStore();

  const [roles, setRoles] = useState<Role[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [formName, setFormName] = useState("");
  const [formDescription, setFormDescription] = useState("");
  const [selectedPermissions, setSelectedPermissions] = useState<string[]>([]);
  const [pageError, setPageError] = useState("");

  useEffect(() => {
    fetchCurrentUser();
  }, [fetchCurrentUser]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  useEffect(() => {
    if (isAuthenticated) {
      loadData();
    }
  }, [isAuthenticated]);

  const loadData = async () => {
    try {
      const [rolesData, permsData] = await Promise.all([
        api.get<Role[]>("/auth/roles/"),
        api.get<Permission[]>("/auth/permissions/"),
      ]);
      setRoles(rolesData);
      setPermissions(permsData);
    } catch {
      setPageError("Failed to load roles. Check your permissions.");
    }
  };

  const handleCreate = async () => {
    try {
      await api.post("/auth/roles/", {
        name: formName,
        description: formDescription,
        permission_ids: selectedPermissions,
      });
      setIsCreating(false);
      setFormName("");
      setFormDescription("");
      setSelectedPermissions([]);
      loadData();
    } catch (err: unknown) {
      setPageError(err instanceof Error ? err.message : "Failed to create role.");
    }
  };

  const handleDelete = async (roleId: string) => {
    if (!confirm("Delete this role? Users with this role will need reassignment.")) return;
    try {
      await api.delete(`/auth/roles/${roleId}/`);
      loadData();
    } catch (err: unknown) {
      setPageError(err instanceof Error ? err.message : "Failed to delete role.");
    }
  };

  const togglePermission = (codename: string) => {
    setSelectedPermissions((prev) =>
      prev.includes(codename)
        ? prev.filter((p) => p !== codename)
        : [...prev, codename],
    );
  };

  if (isLoading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  // Group permissions by resource
  const permissionsByResource = permissions.reduce(
    (acc, perm) => {
      const resource = perm.resource || "other";
      if (!acc[resource]) acc[resource] = [];
      acc[resource].push(perm);
      return acc;
    },
    {} as Record<string, Permission[]>,
  );

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Roles</h1>
            <p className="text-muted-foreground">
              Manage roles and permissions for {user.tenant_slug}
            </p>
          </div>
          <Button onClick={() => setIsCreating(true)}>
            <Icons.plus className="mr-2 h-4 w-4" />
            Create Role
          </Button>
        </div>

        {pageError && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {pageError}
          </div>
        )}

        {/* Create role form */}
        {isCreating && (
          <Card>
            <CardHeader>
              <CardTitle>Create New Role</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="role-name">Role Name</Label>
                <Input
                  id="role-name"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  placeholder="e.g., Senior Doctor"
                />
              </div>
              <div>
                <Label htmlFor="role-desc">Description</Label>
                <Input
                  id="role-desc"
                  value={formDescription}
                  onChange={(e) => setFormDescription(e.target.value)}
                  placeholder="What this role can do"
                />
              </div>

              <div>
                <Label>Permissions</Label>
                <div className="mt-2 max-h-64 space-y-4 overflow-y-auto rounded-md border p-4">
                  {Object.entries(permissionsByResource).map(
                    ([resource, perms]) => (
                      <div key={resource}>
                        <h4 className="mb-1 text-sm font-semibold capitalize">
                          {resource}
                        </h4>
                        <div className="space-y-1">
                          {perms.map((perm) => (
                            <label
                              key={perm.id}
                              className="flex items-center gap-2 text-sm"
                            >
                              <input
                                type="checkbox"
                                checked={selectedPermissions.includes(perm.codename)}
                                onChange={() => togglePermission(perm.codename)}
                                className="rounded"
                              />
                              <span className="text-muted-foreground">
                                {perm.codename}
                              </span>
                            </label>
                          ))}
                        </div>
                      </div>
                    ),
                  )}
                </div>
              </div>

              <div className="flex gap-2">
                <Button onClick={handleCreate}>Save Role</Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setIsCreating(false);
                    setFormName("");
                    setFormDescription("");
                    setSelectedPermissions([]);
                  }}
                >
                  Cancel
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Existing roles */}
        <div className="grid gap-4 md:grid-cols-2">
          {roles.map((role) => (
            <Card
              key={role.id}
              className={`cursor-pointer transition-colors hover:border-primary ${
                selectedRole?.id === role.id ? "border-primary ring-1 ring-primary" : ""
              }`}
              onClick={() => setSelectedRole(role)}
            >
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-lg">{role.name}</CardTitle>
                  <p className="text-xs text-muted-foreground">
                    {role.is_system_role ? "System Role" : "Custom Role"} ·{" "}
                    {role.permissions?.length || 0} permissions
                  </p>
                </div>
                {!role.is_system_role && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-destructive"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(role.id);
                    }}
                  >
                    <Icons.x className="h-4 w-4" />
                  </Button>
                )}
              </CardHeader>
            </Card>
          ))}
        </div>

        {roles.length === 0 && (
          <div className="rounded-lg border border-dashed p-8 text-center text-muted-foreground">
            <p>No roles created yet.</p>
            <p className="text-xs mt-1">
              Create a custom role or use the pre-built system roles.
            </p>
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
