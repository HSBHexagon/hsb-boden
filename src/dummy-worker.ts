export default {
  fetch(request: Request, env: any, ctx: ExecutionContext) {
    return new Response("Dummy worker");
  }
};
