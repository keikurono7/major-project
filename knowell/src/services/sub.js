import { db, collection, query, where, getDocs, doc, setDoc, getDoc } from "./firebase";

export async function getSubjectStructure(subjectId) {
    try {
        const subjectRef = doc(db, 'subjects', subjectId);
        const subjectSnap = await getDoc(subjectRef);
        if (!subjectSnap.exists()) {
            console.warn(`Subject with ID '${subjectId}' not found`);
            return null;
        }

        const subjectData = subjectSnap.data() || {};
        if (!subjectData.name) subjectData.name = `Subject ${subjectId}`;

        const modulesCol = collection(subjectRef, 'modules');
        const modulesSnap = await getDocs(modulesCol);

        const modules = [];
        for (const moduleDoc of modulesSnap.docs) {
            const moduleData = moduleDoc.data() || {};
            moduleData.id = moduleDoc.id;

            const topicsCol = collection(moduleDoc.ref, 'topics');
            const topicsSnap = await getDocs(topicsCol);
            const topics = topicsSnap.docs.map(t => ({ id: t.id, ...(t.data() || {}) }));

            moduleData.topics = topics;
            modules.push(moduleData);
        }

        subjectData.modules = modules;
        console.log(
            `Retrieved subject: ${subjectData.name} with ${modules.reduce((s,m)=>s + (m.topics?.length||0),0)} topics across ${modules.length} modules`
        );
        return subjectData;
    } catch (err) {
        console.error('Error retrieving subject structure:', err);
        return null;
    }
}

export async function getAllSubjects() {
    try {
        console.log("Fetching all subjects from Firestore...");
        const subjectsCol = collection(db, 'subjects');
        const snapshot = await getDocs(subjectsCol);
        console.log(`Fetch completed, processing ${snapshot.size} documents`);
        const subjects = snapshot.docs.map(d => {
            const data = d.data() || {};
            return {
                id: d.id,
                name: data.name || "Unnamed Subject"
            };
        });
        console.log(`Retrieved ${subjects.length} subjects`);
        return subjects;
    } catch (err) {
        console.error("Error retrieving subjects:", err);
        return [];
    }
}

export async function getSubjectModules(subjectId) {
    try {
        const modulesCol = collection(db, 'subjects', subjectId, 'modules');
        const snapshot = await getDocs(modulesCol);
        const modules = snapshot.docs.map(d => {
            const data = d.data() || {};
            return {
                id: d.id,
                name: data.name || "Unnamed Module"
            };
        });
        console.log(`Retrieved ${modules.length} modules for subject ${subjectId}`);
        return modules;
    } catch (err) {
        console.error(`Error retrieving modules for subject ${subjectId}:`, err);
        return [];
    }
}

export async function getModuleTopics(subjectId, moduleId) {
    try {
        const topicsCol = collection(db, 'subjects', subjectId, 'modules', moduleId, 'topics');
        const snapshot = await getDocs(topicsCol);
        const topics = snapshot.docs.map(d => {
            const data = d.data() || {};
            return {
                id: d.id,
                name: data.name || "Unnamed Topic",
                subject_id: subjectId,
                module_id: moduleId
            };
        });
        console.log(`Retrieved ${topics.length} topics for module ${moduleId} in subject ${subjectId}`);
        return topics;
    } catch (err) {
        console.error(`Error retrieving topics for module ${moduleId} in subject ${subjectId}:`, err);
        return [];
    }
}

