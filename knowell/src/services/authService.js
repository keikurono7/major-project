import { db, collection, query, where, getDocs, doc, setDoc, getDoc } from "./firebase";

// helper: sha256 hex (browser crypto)
async function hashPassword(password) {
  const enc = new TextEncoder();
  const data = enc.encode(password);
  const hashBuffer = await crypto.subtle.digest("SHA-256", data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, "0")).join("");
}

// create an id like user_163..._abc
function makeUserId() {
  return `user_${Date.now()}_${Math.random().toString(36).slice(2,8)}`;
}

/**
 * signup(payload)
 * payload may contain: { email, password, fullName | full_name, role }
 * Stores document in collection "users" with id "user_<...>"
 */
export async function signup(payload) {
  const email = payload.email || payload.username;
  const full_name = payload.full_name || payload.fullName || "";
  const role = payload.role || "student";
  if (!email || !payload.password) throw new Error("email and password required");

  // check existing by email
  const usersCol = collection(db, "users");
  const q = query(usersCol, where("email", "==", email));
  const snap = await getDocs(q);
  if (!snap.empty) throw new Error("Email already registered");

  const password_hash = await hashPassword(payload.password);
  const userId = makeUserId();
  const docRef = doc(db, "users", userId);
  const data = {
    email,
    full_name,
    password_hash,
    role,
    created_at: new Date().toISOString()
  };
  await setDoc(docRef, data);
  return { id: userId, email, full_name, role, created_at: data.created_at };
}

/**
 * login(username, password)
 * username is treated as email
 * returns safe user object (omits password_hash)
 */
export async function login(username, password) {
  const usersCol = collection(db, "users");
  const q = query(usersCol, where("email", "==", username));
  const snap = await getDocs(q);
  if (snap.empty) throw new Error("Invalid email or password");
  const docSnap = snap.docs[0];
  const data = docSnap.data();
  const password_hash = await hashPassword(password);
  if (data.password_hash !== password_hash) throw new Error("Invalid email or password");
  return { id: docSnap.id, email: data.email, full_name: data.full_name, role: data.role || "student", created_at: data.created_at };
}

/**
 * getUserById(userId)
 * returns null or user object (without password_hash)
 */
export async function getUserById(userId) {
  if (!userId) return null;
  const ref = doc(db, "users", userId);
  const snap = await getDoc(ref);
  if (!snap.exists()) return null;
  const d = snap.data();
  return { id: snap.id, email: d.email, full_name: d.full_name, role: d.role || "student", created_at: d.created_at };
}

export function logout() {
  // client-side only: clearing local storage handled in auth slice
}

// Add default export object
const authService = {
  register: signup,
  login,
  logout,
  getUserById
};

export default authService;