import * as React from "react"

function cleanHash(hash) {
  return hash.replace(/^#/, "")
}

export const useHash = () => {
    const [hash, setHash] = React.useState(() => cleanHash(window.location.hash));
  
    const hashChangeHandler = React.useCallback(() => {
      setHash(cleanHash(window.location.hash));
    }, []);
  
    React.useEffect(() => {
      window.addEventListener('hashchange', hashChangeHandler);
      return () => {
        window.removeEventListener('hashchange', hashChangeHandler);
      };
    });
  
    const updateHash = React.useCallback(
      newHash => {
        if (newHash !== hash) {
          window.location.hash = newHash ? ("#" + newHash) : '#';
        }
      },
      [hash]
    );
  
    return [hash, updateHash];
  };