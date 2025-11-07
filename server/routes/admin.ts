import type { Express, Request, Response } from "express";
import { db } from "../db";
import { users, inviteCodes, auditLogs } from "@shared/schema";
import { eq, desc, count, sql } from "drizzle-orm";
import { requireAdmin, requireSuperAdmin } from "../middleware/rbac";

/**
 * Admin Routes - Protected routes for admin/superadmin users
 * MVP: User management, Invite codes, Basic analytics
 */

export function registerAdminRoutes(app: Express) {
  
  // ============================================
  // USER MANAGEMENT
  // ============================================
  
  // Get all users (admin/superadmin only)
  app.get('/api/admin/users', requireAdmin, async (req: Request, res: Response) => {
    try {
      const allUsers = await db
        .select({
          id: users.id,
          username: users.username,
          email: users.email,
          role: users.role,
          availableInvites: users.availableInvites,
          createdAt: users.createdAt,
        })
        .from(users)
        .orderBy(desc(users.createdAt));

      res.json(allUsers);
    } catch (error) {
      console.error('[Admin] Error fetching users:', error);
      res.status(500).json({ detail: 'Erro ao buscar usuários' });
    }
  });

  // Update user role (superadmin only)
  app.patch('/api/admin/users/:userId/role', requireSuperAdmin, async (req: Request, res: Response) => {
    try {
      const { userId } = req.params;
      const { role } = req.body;

      // Validate role
      if (!['user', 'admin', 'superadmin'].includes(role)) {
        return res.status(400).json({ detail: 'Invalid role' });
      }

      // Fetch current user to capture old role BEFORE update
      const [currentUser] = await db
        .select({ role: users.role })
        .from(users)
        .where(eq(users.id, userId))
        .limit(1);

      if (!currentUser) {
        return res.status(404).json({ detail: 'User not found' });
      }

      const oldRole = currentUser.role;

      // Update user role (return only safe fields, exclude password)
      const [updatedUser] = await db
        .update(users)
        .set({ role })
        .where(eq(users.id, userId))
        .returning({
          id: users.id,
          username: users.username,
          email: users.email,
          role: users.role,
          availableInvites: users.availableInvites,
          createdAt: users.createdAt,
        });

      // Log audit event with correct old role
      await db.insert(auditLogs).values({
        userId: req.session.userId!,
        action: 'user_role_changed',
        resourceType: 'user',
        resourceId: userId,
        metadata: { oldRole, newRole: role },
        ipAddress: req.ip,
      });

      res.json(updatedUser);
    } catch (error) {
      console.error('[Admin] Error updating user role:', error);
      res.status(500).json({ detail: 'Erro ao atualizar role do usuário' });
    }
  });

  // ============================================
  // INVITE CODE MANAGEMENT
  // ============================================
  
  // Get all invite codes
  app.get('/api/admin/invites', requireAdmin, async (req: Request, res: Response) => {
    try {
      const allInvites = await db
        .select()
        .from(inviteCodes)
        .orderBy(desc(inviteCodes.createdAt));

      res.json(allInvites);
    } catch (error) {
      console.error('[Admin] Error fetching invites:', error);
      res.status(500).json({ detail: 'Erro ao buscar códigos de convite' });
    }
  });

  // Create invite code
  app.post('/api/admin/invites', requireAdmin, async (req: Request, res: Response) => {
    try {
      const { code } = req.body;

      if (!code || code.length > 16) {
        return res.status(400).json({ detail: 'Code must be 1-16 characters' });
      }

      // Always use current session userId as creator (prevent privilege escalation)
      const [newInvite] = await db
        .insert(inviteCodes)
        .values({
          code,
          creatorId: req.session.userId!,
        })
        .returning();

      // Log audit event
      await db.insert(auditLogs).values({
        userId: req.session.userId!,
        action: 'invite_code_created',
        resourceType: 'invite_code',
        resourceId: newInvite.id,
        metadata: { code: newInvite.code },
        ipAddress: req.ip,
      });

      res.status(201).json(newInvite);
    } catch (error: any) {
      console.error('[Admin] Error creating invite:', error);
      
      // Handle unique constraint violation
      if (error?.code === '23505') {
        return res.status(400).json({ detail: 'Código de convite já existe' });
      }

      res.status(500).json({ detail: 'Erro ao criar código de convite' });
    }
  });

  // ============================================
  // ANALYTICS & STATS
  // ============================================
  
  // Get admin dashboard stats
  app.get('/api/admin/stats', requireAdmin, async (req: Request, res: Response) => {
    try {
      // Total users
      const [{ totalUsers }] = await db
        .select({ totalUsers: count() })
        .from(users);

      // Total invites
      const [{ totalInvites }] = await db
        .select({ totalInvites: count() })
        .from(inviteCodes);

      // Used invites
      const [{ usedInvites }] = await db
        .select({ usedInvites: count() })
        .from(inviteCodes)
        .where(sql`${inviteCodes.usedBy} IS NOT NULL`);

      // Role distribution
      const roleDistribution = await db
        .select({
          role: users.role,
          count: count(),
        })
        .from(users)
        .groupBy(users.role);

      res.json({
        totalUsers,
        totalInvites,
        usedInvites,
        availableInvites: totalInvites - usedInvites,
        roleDistribution,
      });
    } catch (error) {
      console.error('[Admin] Error fetching stats:', error);
      res.status(500).json({ detail: 'Erro ao buscar estatísticas' });
    }
  });

  // ============================================
  // AUDIT LOGS
  // ============================================
  
  // Get audit logs
  app.get('/api/admin/audit-logs', requireAdmin, async (req: Request, res: Response) => {
    try {
      const limit = parseInt(req.query.limit as string) || 100;
      const offset = parseInt(req.query.offset as string) || 0;

      const logs = await db
        .select()
        .from(auditLogs)
        .orderBy(desc(auditLogs.createdAt))
        .limit(limit)
        .offset(offset);

      res.json(logs);
    } catch (error) {
      console.error('[Admin] Error fetching audit logs:', error);
      res.status(500).json({ detail: 'Erro ao buscar logs de auditoria' });
    }
  });
}
