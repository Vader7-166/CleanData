import { useState, useEffect } from 'react';

/**
 * A custom hook that behaves like useState but persists the value in localStorage.
 * 
 * @param {string} key - The localStorage key to use
 * @param {any} initialValue - The initial value if no value is found in localStorage
 * @returns {[any, Function]} - The state and setter function
 */
export const usePersistedState = (key, initialValue) => {
  // Get initial value from localStorage or fallback to initialValue
  const [state, setState] = useState(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });

  // Sync with localStorage whenever state changes
  useEffect(() => {
    try {
      window.localStorage.setItem(key, JSON.stringify(state));
    } catch (error) {
      console.error(`Error setting localStorage key "${key}":`, error);
    }
  }, [key, state]);

  return [state, setState];
};

export default usePersistedState;
