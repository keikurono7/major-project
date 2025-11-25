import { initializeApp, getApps } from "firebase/app";
import {
  getFirestore,
  collection,
  addDoc,
  getDocs,
  getDoc,
  setDoc,
  query,
  where,
  updateDoc,
  doc,
  deleteDoc,
  Timestamp
} from "firebase/firestore";
import { getStorage, ref, uploadBytes, getBytes, listAll, getMetadata } from "firebase/storage";
import { getAuth } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyB-c_DQbX00cZCOHOkcEio47kqp1ZkDdtM",
  authDomain: "atomic-lens-471613-m4.firebaseapp.com",
  projectId: "atomic-lens-471613-m4",
  storageBucket: "atomic-lens-471613-m4.appspot.com",
  messagingSenderId: "958164135424",
  appId: "1:958164135424:web:ae4732e3d01322ce48f2e5",
  measurementId: "G-7RG43G0WJX"
};

const app = initializeApp(firebaseConfig);

export const db = getFirestore(app);
export const storage = getStorage(app);
export const auth = getAuth(app);

// Export Firestore functions
export {
  collection,
  addDoc,
  getDocs,
  setDoc,
  query,
  where,
  updateDoc,
  doc,
  deleteDoc,
  Timestamp,
  ref,
  uploadBytes,
  getBytes,
  listAll,
  getMetadata,
  getDoc
};

export default app;

