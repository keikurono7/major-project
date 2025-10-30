import { db } from './firebase';
import {
  collection,
  getDocs,
  addDoc,
  doc,
  updateDoc,
  query,
  where,
  arrayUnion,
  serverTimestamp
} from 'firebase/firestore';

export const getClasses = async () => {
  const col = collection(db, 'classes');
  const snapshot = await getDocs(col);
  return snapshot.docs.map(d => ({ id: d.id, ...d.data() }));
};

export const getClassesForUser = async (userId, role) => {
  const col = collection(db, 'classes');
  if (!userId) return [];
  if (role === 'teacher') {
    const q = query(col, where('teacherId', '==', userId));
    const snap = await getDocs(q);
    return snap.docs.map(d => ({ id: d.id, ...d.data() }));
  } else {
    const q = query(col, where('students', 'array-contains', userId));
    const snap = await getDocs(q);
    return snap.docs.map(d => ({ id: d.id, ...d.data() }));
  }
};

export const createClass = async (name, teacherId = null) => {
  const col = collection(db, 'classes');
  const docRef = await addDoc(col, {
    name,
    teacherId: teacherId || null,
    students: [],
    createdAt: serverTimestamp(),
  });
  return { id: docRef.id, name, teacherId: teacherId || null };
};

export const setClassTeacher = async (classId, teacherId) => {
  if (!classId) throw new Error('classId required');
  const d = doc(db, 'classes', classId);
  await updateDoc(d, { teacherId });
  return true;
};

export const addStudentToClass = async (classId, studentId) => {
  if (!classId) throw new Error('classId required');
  const d = doc(db, 'classes', classId);
  await updateDoc(d, { students: arrayUnion(studentId) });
  return true;
};