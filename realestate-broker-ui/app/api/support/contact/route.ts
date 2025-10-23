import { validateToken } from "@/lib/token-utils";
import { cookies } from "next/headers";
import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const body = await req.json();

  const cookieStore = await cookies();
  const token = cookieStore.get("access_token")?.value;
  const tokenValidation = validateToken(token);
  if (!tokenValidation.isValid) {
    console.log('API Contact - Token validation failed:', tokenValidation.error);
    const response = NextResponse.json({ error: 'Unauthorized - Token expired or invalid' }, { status: 401 });
    response.cookies.delete('access_token');
    response.cookies.delete('refresh_token');
    return response;
  }


  const res = await fetch(`${process.env.BACKEND_URL}/api/support/contact`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    body: JSON.stringify(body),
  });
  return NextResponse.json(await res.json(), { status: res.status });
}
