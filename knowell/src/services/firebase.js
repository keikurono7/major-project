import { initializeApp, getApps } from "firebase/app";
import {
  getFirestore,
  collection,
  getDocs,
  addDoc,
  setDoc,
  getDoc,
  doc,
  updateDoc,
  query,
  where,
  arrayUnion,
  serverTimestamp
} from 'firebase/firestore';

const firebaseConfig = {
  apiKey: "AIzaSyB-c_DQbX00cZCOHOkcEio47kqp1ZkDdtM",
  authDomain: "atomic-lens-471613-m4.firebaseapp.com",
  projectId: "atomic-lens-471613-m4",
  storageBucket: "atomic-lens-471613-m4.firebasestorage.app",
  messagingSenderId: "958164135424",
  appId: "1:958164135424:web:ae4732e3d01322ce48f2e5",
  measurementId: "G-7RG43G0WJX"
};


if (!getApps().length) initializeApp(firebaseConfig);
const db = getFirestore();

export { db, collection, query, where, getDocs, doc, setDoc, getDoc };

