/** @typedef {import('../client/client').IntricError} IntricError */
/** @typedef {import('../types/resources').Job} Job */

/**
 * @param {import('../client/client').Client} client Provide a client with which to call the endpoints
 */
export function initJobs(client) {
  return {
    /**
     * List all jobs.
     * @param {{includeCompleted: boolean}} [params] Include completed jobs in response?
     * @returns {Promise<Job[]>}
     * @throws {IntricError}
     * */
    list: async (params) => {
      const include_completed = params?.includeCompleted ?? false;
      const res = await client.fetch("/api/v1/jobs/", {
        method: "get",
        params: { query: { include_completed } }
      });
      return res.items;
    },

    /**
     * Get info of a job via its id.
     * @param  {{id: string} | Job} job job
     * @returns {Promise<Job>} Current info about the queried job
     * @throws {IntricError}
     * */
    get: async (job) => {
      const { id } = job;
      const res = await client.fetch("/api/v1/jobs/{id}/", {
        method: "get",
        params: { path: { id } }
      });
      return res;
    }
  };
}