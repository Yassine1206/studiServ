import { Navigate } from 'react-router-dom';

function PrivateRoute({ isAuthenticated, requiredRole, userRole, children }) {
  if (!isAuthenticated) {
    return <Navigate to="/signin" replace />;
  }

  if (requiredRole && userRole !== requiredRole) {
    return <Navigate to="/" replace />;
  }

  return children;
}

export default PrivateRoute;
