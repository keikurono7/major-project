import { db, doc, getDoc } from './firebase';
import { getAllSubjects, getSubjectModules, getModuleTopics } from './sub';

/**
 * Default BKT params (match backend defaults)
 */
function getDefaultBktParams() {
  return {
    p_L0: 0.0,
    p_L: 0.0,
    p_T: 0.1,
    p_G: 0.2,
    p_S: 0.1,
    attempts: 0,
    correct: 0
  };
}

/**
 * Read student's BKT parameters for a topic directly from Firestore.
 * Mirrors gcp/firebase_ops.get_student_bkt_params logic but runs client-side.
 * Returns full param object (with defaults merged).
 */
export async function getStudentBktParamsFromFirestore(studentId, topicId) {
  try {
    if (!db || !studentId || !topicId) return getDefaultBktParams();

    const userRef = doc(db, 'users', studentId);
    const userSnap = await getDoc(userRef);
    if (!userSnap.exists()) return getDefaultBktParams();

    const userData = userSnap.data() || {};

    // 1) mastery_summary quick path: mastery_summary.{subject_id}.{topic_id} => { mastery: <val> }
    if (userData.mastery_summary && typeof userData.mastery_summary === 'object') {
      for (const subjId of Object.keys(userData.mastery_summary)) {
        const topics = userData.mastery_summary[subjId] || {};
        if (topicId in topics) {
          const topicData = topics[topicId] || {};
          const params = { ...getDefaultBktParams() };
          params.p_L = Number(topicData.mastery ?? topicData.mastery_probability ?? params.p_L) || params.p_L;
          return params;
        }
      }
    }

    // 2) mastery.unknown_topics.{topicId}
    if (userData.mastery && userData.mastery.unknown_topics && userData.mastery.unknown_topics[topicId]) {
      return { ...getDefaultBktParams(), ...userData.mastery.unknown_topics[topicId] };
    }

    // 3) full mastery structure: mastery.subjects.{subject}.modules.{module}.topics.{topic}
    if (userData.mastery && userData.mastery.subjects && typeof userData.mastery.subjects === 'object') {
      for (const subjId of Object.keys(userData.mastery.subjects)) {
        const subj = userData.mastery.subjects[subjId] || {};
        if (!subj.modules || typeof subj.modules !== 'object') continue;
        for (const modId of Object.keys(subj.modules)) {
          const mod = subj.modules[modId] || {};
          if (!mod.topics || typeof mod.topics !== 'object') continue;
          if (topicId in mod.topics) {
            const params = { ...getDefaultBktParams(), ...mod.topics[topicId] };
            // ensure required keys
            const defaults = getDefaultBktParams();
            for (const k of Object.keys(defaults)) {
              if (!(k in params)) params[k] = defaults[k];
            }
            return params;
          }
        }
      }
    }

    // fallback
    return getDefaultBktParams();
  } catch (err) {
    console.warn('getStudentBktParamsFromFirestore failed', studentId, topicId, err);
    return getDefaultBktParams();
  }
}

/**
 * Get BKT/mastery score for a single topic for a student.
 * Now reads directly from Firestore client-side.
 * Returns number in range 0..1 (falls back to 0).
 */
export async function getTopicBkt(studentId, topicId) {
  try {
    const params = await getStudentBktParamsFromFirestore(studentId, topicId);
    const val = params.mastery_probability ?? params.p_L ?? params.p_L0 ?? 0;
    return Number(val) || 0;
  } catch (err) {
    console.warn('getTopicBkt failed', studentId, topicId, err);
    return 0;
  }
}

/**
 * Compute module progress (adds bkt_score to each topic and returns module average).
 * module: { id, name, topics: [ { id, name, ... } ] }
 */
export async function computeModuleProgress(studentId, subjectId, module) {
  const topics = module.topics || [];
  const topicsWithBkt = await Promise.all(
    topics.map(async (t) => {
      const bkt = await getTopicBkt(studentId, t.id);
      return { ...t, bkt_score: bkt };
    })
  );

  const avg =
    topicsWithBkt.length > 0
      ? topicsWithBkt.reduce((s, t) => s + (t.bkt_score || 0), 0) / topicsWithBkt.length
      : 0;

  return { ...module, topics: topicsWithBkt, avg_bkt: avg };
}

/**
 * Compute subject-level progress by computing each module via computeModuleProgress.
 * subject: { id, name, modules: [ { id, name } ] }
 * Returns subject with modules populated with topics and averages and subject avg.
 */
export async function computeSubjectProgress(studentId, subject) {
  const modules = subject.modules || [];
  const modulesWithProgress = [];
  for (const module of modules) {
    const modWith = await computeModuleProgress(studentId, subject.id, module);
    modulesWithProgress.push(modWith);
  }

  const allTopicScores = modulesWithProgress.flatMap((m) => m.topics.map((t) => t.bkt_score || 0));
  const subjectAvg =
    allTopicScores.length > 0 ? allTopicScores.reduce((s, v) => s + v, 0) / allTopicScores.length : 0;

  return { ...subject, modules: modulesWithProgress, avg_bkt: subjectAvg };
}

/**
 * Compute progress for all subjects for a student.
 * Fetches subjects -> modules -> topics using sub.js then computes BKT-based progress.
 * Returns array of subjects with populated modules/topics and averages.
 */
export async function computeAllSubjectsProgress(studentId) {
  try {
    const subjects = await getAllSubjects();
    if (!subjects || subjects.length === 0) return [];

    const result = [];
    for (const subject of subjects) {
      const modules = await getSubjectModules(subject.id);
      const modulesWithTopics = [];
      for (const module of modules) {
        const topics = await getModuleTopics(subject.id, module.id);
        modulesWithTopics.push({ ...module, topics });
      }
      const subjectWithProgress = await computeSubjectProgress(studentId, { ...subject, modules: modulesWithTopics });
      result.push(subjectWithProgress);
    }
    return result;
  } catch (err) {
    console.error('computeAllSubjectsProgress failed', err);
    return [];
  }
}

export default {
  getStudentBktParamsFromFirestore,
  getTopicBkt,
  computeModuleProgress,
  computeSubjectProgress,
  computeAllSubjectsProgress
};