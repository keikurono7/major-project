import { 
  db,
  storage,
  collection, 
  addDoc, 
  getDocs, 
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
  getMetadata
} from './firebase';

// Create a new project
export const createProject = async (projectData, creatorId) => {
  try {
    const projectsCollection = collection(db, 'projects');
    const docRef = await addDoc(projectsCollection, {
      ...projectData,
      creatorId,
      createdAt: Timestamp.now(),
      updatedAt: Timestamp.now(),
      status: 'active'
    });
    return docRef.id;
  } catch (error) {
    console.error('Error creating project:', error);
    throw error;
  }
};

// Get projects created by a teacher
export const getTeacherProjects = async (teacherId) => {
  try {
    const projectsCollection = collection(db, 'projects');
    const q = query(projectsCollection, where('creatorId', '==', teacherId));
    const querySnapshot = await getDocs(q);
    return querySnapshot.docs.map(doc => ({
      id: doc.id,
      ...doc.data()
    }));
  } catch (error) {
    console.error('Error fetching teacher projects:', error);
    throw error;
  }
};

// Get projects assigned to a student
export const getStudentProjects = async (studentId) => {
  try {
    const projectsCollection = collection(db, 'projects');
    const q = query(
      projectsCollection,
      where('assignedStudents', 'array-contains', studentId)
    );
    const querySnapshot = await getDocs(q);
    return querySnapshot.docs.map(doc => ({
      id: doc.id,
      ...doc.data()
    }));
  } catch (error) {
    console.error('Error fetching student projects:', error);
    throw error;
  }
};

// Update project details
export const updateProject = async (projectId, updates) => {
  try {
    const projectRef = doc(db, 'projects', projectId);
    await updateDoc(projectRef, {
      ...updates,
      updatedAt: Timestamp.now()
    });
  } catch (error) {
    console.error('Error updating project:', error);
    throw error;
  }
};

// Assign students to project
export const assignStudentsToProject = async (projectId, studentIds) => {
  try {
    const projectRef = doc(db, 'projects', projectId);
    await updateDoc(projectRef, {
      assignedStudents: studentIds,
      updatedAt: Timestamp.now()
    });
  } catch (error) {
    console.error('Error assigning students:', error);
    throw error;
  }
};

// Delete project
export const deleteProject = async (projectId) => {
  try {
    const projectRef = doc(db, 'projects', projectId);
    await deleteDoc(projectRef);
  } catch (error) {
    console.error('Error deleting project:', error);
    throw error;
  }
};

// Submit project files
export const submitProjectFiles = async (projectId, studentId, files) => {
  try {
    const submissionId = `${projectId}_${studentId}_${Date.now()}`;
    const uploadPromises = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const filePath = `submissions/${projectId}/${studentId}/${submissionId}/${file.name}`;
      const fileRef = ref(storage, filePath);
      uploadPromises.push(uploadBytes(fileRef, file));
    }

    await Promise.all(uploadPromises);

    // Create submission record in Firestore
    const submissionsCollection = collection(db, 'submissions');
    const docRef = await addDoc(submissionsCollection, {
      projectId,
      studentId,
      submissionId,
      fileCount: files.length,
      files: files.map(f => f.name),
      status: 'submitted',
      createdAt: Timestamp.now(),
      feedback: null,
      aiEvaluation: null
    });

    return docRef.id;
  } catch (error) {
    console.error('Error submitting files:', error);
    throw error;
  }
};

// Get submissions for a project
export const getProjectSubmissions = async (projectId) => {
  try {
    const submissionsCollection = collection(db, 'submissions');
    const q = query(submissionsCollection, where('projectId', '==', projectId));
    const querySnapshot = await getDocs(q);
    return querySnapshot.docs.map(doc => ({
      id: doc.id,
      ...doc.data()
    }));
  } catch (error) {
    console.error('Error fetching submissions:', error);
    throw error;
  }
};

// Get student's submission for a project
export const getStudentSubmission = async (projectId, studentId) => {
  try {
    const submissionsCollection = collection(db, 'submissions');
    const q = query(
      submissionsCollection,
      where('projectId', '==', projectId),
      where('studentId', '==', studentId)
    );
    const querySnapshot = await getDocs(q);
    return querySnapshot.docs.map(doc => ({
      id: doc.id,
      ...doc.data()
    }));
  } catch (error) {
    console.error('Error fetching student submission:', error);
    throw error;
  }
};

// Get submission files
export const getSubmissionFiles = async (projectId, studentId, submissionId) => {
  try {
    const folderRef = ref(
      storage,
      `submissions/${projectId}/${studentId}/${submissionId}`
    );
    const fileList = await listAll(folderRef);
    
    const files = [];
    for (const item of fileList.items) {
      const metadata = await getMetadata(item);
      files.push({
        name: item.name,
        fullPath: item.fullPath,
        size: metadata.size,
        timeCreated: metadata.timeCreated
      });
    }
    return files;
  } catch (error) {
    console.error('Error fetching submission files:', error);
    throw error;
  }
};

// Download file content
export const getFileContent = async (filePath) => {
  try {
    const fileRef = ref(storage, filePath);
    const bytes = await getBytes(fileRef);
    return bytes;
  } catch (error) {
    console.error('Error downloading file:', error);
    throw error;
  }
};

// Update submission with feedback
export const updateSubmissionFeedback = async (submissionId, feedback) => {
  try {
    const submissionRef = doc(db, 'submissions', submissionId);
    await updateDoc(submissionRef, {
      feedback,
      status: 'reviewed',
      reviewedAt: Timestamp.now()
    });
  } catch (error) {
    console.error('Error updating submission feedback:', error);
    throw error;
  }
};

// Update submission with AI evaluation
export const updateSubmissionAIEvaluation = async (submissionId, aiEvaluation) => {
  try {
    const submissionRef = doc(db, 'submissions', submissionId);
    await updateDoc(submissionRef, {
      aiEvaluation,
      status: 'ai_evaluated',
      aiEvaluatedAt: Timestamp.now()
    });
  } catch (error) {
    console.error('Error updating AI evaluation:', error);
    throw error;
  }
};