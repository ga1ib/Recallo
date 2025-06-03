import React from 'react';

export default function Loader() {
  return (
    <div className="flex justify-center py-2">
      <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-indigo-600"></div>
    </div>
  );
}
