// src/contexts/AuthContext.js
import React, { createContext, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { loginUser, logoutUser, signupUser, setUser } from "../store/authSlice";

export const AuthContext = createContext({
  currentUser: null,
  loading: true,
  login: async () => {},
  logout: async () => {},
  signup: async () => {}
});

export const AuthProvider = ({ children }) => {
  const dispatch = useDispatch();
  const auth = useSelector((s) => s.auth);
  const loading = auth.status === "loading";

  // Check for cached user on mount
  useEffect(() => {
    const cachedUser = localStorage.getItem('knowell_user');
    if (cachedUser && !auth.currentUser) {
      try {
        const userData = JSON.parse(cachedUser);
        dispatch(setUser(userData));
      } catch (err) {
        console.error('Failed to restore user session', err);
        localStorage.removeItem('knowell_user');
      }
    }
  }, [dispatch, auth.currentUser]);

  const login = async (username, password) => {
    const res = await dispatch(loginUser({ username, password }));
    if (res.error) {
      const msg = res.payload || (res.error && res.error.message) || "Login failed";
      throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
    }
    // Cache user after successful login
    if (res.payload) {
      localStorage.setItem('knowell_user', JSON.stringify(res.payload));
    }
    return res.payload;
  };

  const signup = async (payload) => {
    const res = await dispatch(signupUser(payload));
    if (res.error) {
      const msg = res.payload || (res.error && res.error.message) || "Signup failed";
      throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
    }
    // Cache user after successful signup
    if (res.payload) {
      localStorage.setItem('knowell_user', JSON.stringify(res.payload));
    }
    return res.payload;
  };

  const logout = async () => {
    await dispatch(logoutUser());
    localStorage.removeItem('knowell_user');
  };

  return (
    <AuthContext.Provider value={{ currentUser: auth.currentUser, loading, login, logout, signup }}>
      {children}
    </AuthContext.Provider>
  );
};
