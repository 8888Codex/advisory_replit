import { Request, Response, NextFunction } from 'express';

/**
 * RBAC Middleware - Role-Based Access Control
 * Protects routes based on user roles: user, admin, superadmin
 */

export function requireAuth(req: Request, res: Response, next: NextFunction) {
  if (!req.session?.userId) {
    return res.status(401).json({ detail: 'Authentication required' });
  }
  next();
}

export function requireAdmin(req: Request, res: Response, next: NextFunction) {
  if (!req.session?.userId) {
    return res.status(401).json({ detail: 'Authentication required' });
  }

  const userRole = req.session.user?.role || 'user';
  
  if (userRole !== 'admin' && userRole !== 'superadmin') {
    return res.status(403).json({ detail: 'Admin access required' });
  }

  next();
}

export function requireSuperAdmin(req: Request, res: Response, next: NextFunction) {
  if (!req.session?.userId) {
    return res.status(401).json({ detail: 'Authentication required' });
  }

  const userRole = req.session.user?.role || 'user';
  
  if (userRole !== 'superadmin') {
    return res.status(403).json({ detail: 'Superadmin access required' });
  }

  next();
}
